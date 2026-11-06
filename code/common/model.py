"""Text generation behind one small interface, with two interchangeable backends.

* ``VLLMGenerator`` - fast batched inference with vLLM, used on the KGP GPU servers.
* ``HFGenerator``   - plain Hugging Face transformers, used on Colab (T4 in 4-bit)
                      or any GPU where vLLM is not available.

Both take a list of ``Request`` objects (prompt + decoding settings + seed) and
return one ``Output`` per request, in the same order. Tasks never talk to vLLM or
transformers directly; ``load_generator(model, backend=...)`` picks one.
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass

from common.config import MAX_MODEL_LEN, SEED, Decoding, ModelSpec, model_spec
from common.prompts import Prompt


@dataclass(frozen=True)
class Request:
    prompt: Prompt
    decoding: Decoding
    seed: int = SEED


@dataclass(frozen=True)
class Output:
    text: str            # generated continuation (without the prompt or prefill)
    n_tokens: int        # number of generated tokens
    finish_reason: str   # "stop" (model ended its turn) or "length" (hit max_new_tokens)


class Generator:
    """Shared logic: turning a Prompt into the exact text the model sees."""

    tokenizer = None  # set by subclasses
    spec: ModelSpec   # the model being run

    def render(self, prompt: Prompt) -> str:
        """Apply the model's chat template, open the assistant turn, then append the
        prefill. Appending the prefill ourselves (instead of passing it as an
        unfinished assistant message) keeps it byte-exact: the Llama template
        would otherwise trim trailing whitespace."""
        text = self.tokenizer.apply_chat_template(
            list(prompt.messages), tokenize=False, add_generation_prompt=True,
            **dict(self.spec.chat_template_kwargs))
        return text + (prompt.prefill or "")

    def encode(self, text: str) -> list[int]:
        # The chat template already adds any start token (<|begin_of_text|> for Llama), so no extra BOS.
        return self.tokenizer(text, add_special_tokens=False)["input_ids"]

    def count_tokens(self, text: str) -> int:
        return len(self.encode(text))

    def generate(self, requests: list[Request], desc: str = "") -> list[Output]:
        raise NotImplementedError


def _load_tokenizer(spec: ModelSpec):
    from transformers import AutoTokenizer

    return AutoTokenizer.from_pretrained(spec.hf_id, revision=spec.revision)


def auto_gpu_mem_util(margin_gib: float = 1.5) -> float:
    """Fraction of GPU memory vLLM may claim, based on what is free *right now*.

    The KGP GPU boxes are shared and other users' jobs hold memory, so a fixed
    fraction such as 0.9 would fail. We read free memory with NVML (no CUDA
    context is created), leave a safety margin, and use the tightest GPU.
    """
    import pynvml

    pynvml.nvmlInit()
    visible = os.environ.get("CUDA_VISIBLE_DEVICES")
    indices = [int(x) for x in visible.split(",")] if visible else range(pynvml.nvmlDeviceGetCount())
    fractions = []
    for i in indices:
        info = pynvml.nvmlDeviceGetMemoryInfo(pynvml.nvmlDeviceGetHandleByIndex(i))
        fractions.append((info.free - margin_gib * 2**30) / info.total)
    pynvml.nvmlShutdown()
    return max(0.10, min(0.90, min(fractions)))


class VLLMGenerator(Generator):
    def __init__(self, spec: ModelSpec, tensor_parallel: int = 1, gpu_mem_util: float | None = None,
                 enforce_eager: bool = True, max_model_len: int = MAX_MODEL_LEN):
        from vllm import LLM

        self.spec = spec
        util = gpu_mem_util or auto_gpu_mem_util()
        print(f"[model] vLLM {spec.hf_id}: tp={tensor_parallel} gpu_memory_utilization={util:.2f} "
              f"eager={enforce_eager}", flush=True)
        self.tokenizer = _load_tokenizer(spec)
        self.llm = LLM(model=spec.hf_id, revision=spec.revision, tokenizer_revision=spec.revision,
                       dtype="bfloat16", tensor_parallel_size=tensor_parallel,
                       gpu_memory_utilization=util, max_model_len=max_model_len,
                       seed=SEED, enforce_eager=enforce_eager)

    def generate(self, requests: list[Request], desc: str = "") -> list[Output]:
        from vllm import SamplingParams

        if not requests:
            return []
        start = time.time()
        # Pass token ids (not text) so vLLM does not add a second BOS token.
        prompts = [{"prompt_token_ids": self.encode(self.render(r.prompt))} for r in requests]
        # One SamplingParams per request: each item gets its own seed, so results do
        # not depend on batch composition or order.
        params = [SamplingParams(temperature=r.decoding.temperature, top_p=r.decoding.top_p,
                                 max_tokens=r.decoding.max_new_tokens, seed=r.seed)
                  for r in requests]
        results = self.llm.generate(prompts, params, use_tqdm=False)
        outputs = [Output(res.outputs[0].text, len(res.outputs[0].token_ids),
                          res.outputs[0].finish_reason or "stop") for res in results]
        print(f"[gen] {desc or 'generate'}: {len(requests)} requests in {time.time() - start:.0f}s",
              flush=True)
        return outputs


class HFGenerator(Generator):
    """transformers backend. Slower than vLLM but runs anywhere, including 4-bit on a
    Colab T4. Sampling uses one seed per batch, so sampled outputs will differ from
    the vLLM runs; greedy outputs should match up to numerical noise."""

    def __init__(self, spec: ModelSpec, quant: str | None = None, batch_size: int = 16):
        import torch
        from transformers import AutoModelForCausalLM, BitsAndBytesConfig

        self.spec = spec
        self.batch_size = batch_size
        self.tokenizer = _load_tokenizer(spec)
        self.tokenizer.padding_side = "left"  # decoder-only models must be padded on the left
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
        kwargs = {"revision": spec.revision, "dtype": dtype, "device_map": "auto"}
        if quant == "4bit":
            kwargs["quantization_config"] = BitsAndBytesConfig(
                load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_compute_dtype=dtype)
        print(f"[model] transformers: dtype={dtype} quant={quant} batch_size={batch_size}", flush=True)
        self.model = AutoModelForCausalLM.from_pretrained(spec.hf_id, **kwargs).eval()
        eos = self.model.generation_config.eos_token_id
        self.stop_ids = set(eos if isinstance(eos, list) else [eos])

    def generate(self, requests: list[Request], desc: str = "") -> list[Output]:
        import torch

        if not requests:
            return []
        start = time.time()
        texts = [self.render(r.prompt) for r in requests]
        # Batch requests with identical decoding settings, shortest prompts together
        # to minimise padding.
        order = sorted(range(len(requests)), key=lambda i: (
            requests[i].decoding.temperature, requests[i].decoding.top_p,
            requests[i].decoding.max_new_tokens, len(texts[i])))
        outputs: list[Output | None] = [None] * len(requests)
        batch: list[int] = []
        for pos, idx in enumerate(order):
            batch.append(idx)
            last = pos == len(order) - 1
            if last or len(batch) == self.batch_size or requests[order[pos + 1]].decoding != requests[idx].decoding:
                self._run_batch(batch, requests, texts, outputs, torch)
                batch = []
        print(f"[gen] {desc or 'generate'}: {len(requests)} requests in {time.time() - start:.0f}s",
              flush=True)
        return outputs  # type: ignore[return-value]

    def _run_batch(self, batch, requests, texts, outputs, torch) -> None:
        dec = requests[batch[0]].decoding
        enc = self.tokenizer([texts[i] for i in batch], return_tensors="pt", padding=True,
                             add_special_tokens=False).to(self.model.device)
        kwargs = {"max_new_tokens": dec.max_new_tokens, "pad_token_id": self.tokenizer.pad_token_id}
        if dec.temperature > 0:
            torch.manual_seed(requests[batch[0]].seed)
            kwargs.update(do_sample=True, temperature=dec.temperature, top_p=dec.top_p)
        else:
            kwargs.update(do_sample=False, temperature=None, top_p=None)
        with torch.no_grad():
            generated = self.model.generate(**enc, **kwargs)[:, enc["input_ids"].shape[1]:]
        for row, idx in zip(generated.tolist(), batch):
            cut = next((j for j, tok in enumerate(row) if tok in self.stop_ids), None)
            ids = row if cut is None else row[:cut]
            outputs[idx] = Output(self.tokenizer.decode(ids, skip_special_tokens=True), len(ids),
                                  "length" if cut is None else "stop")


def load_generator(model: str, backend: str = "vllm", tp: int = 1, gpu_mem_util: float | None = None,
                   eager: bool = True, quant: str | None = None, batch_size: int = 16) -> Generator:
    """Load `model` (a key of config.MODELS) with vLLM (cluster) or transformers (e.g. Colab;
    quant="4bit" fits an 8B model on a T4)."""
    spec = model_spec(model)
    if backend == "vllm":
        return VLLMGenerator(spec, tensor_parallel=tp, gpu_mem_util=gpu_mem_util, enforce_eager=eager)
    return HFGenerator(spec, quant=quant, batch_size=batch_size)
