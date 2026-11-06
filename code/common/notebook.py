"""Helpers shared by the three task notebooks: live-run setup, model loading, display."""
from __future__ import annotations

import os
import subprocess
import sys

from common.config import MODELS
from common.io_utils import results_dir

COLAB_PACKAGES = ["transformers==5.17.0", "accelerate==1.15.0", "bitsandbytes==0.50.2",
                  "huggingface_hub==1.33.0"]


def in_colab() -> bool:
    return "google.colab" in sys.modules


def get_secret(name: str) -> str | None:
    """Colab secret if available, else environment variable, else None."""
    try:
        from google.colab import userdata
        return userdata.get(name)
    except Exception:
        return os.environ.get(name)


def model_settings(backend: str = "auto") -> dict:
    """How to load the model here. vLLM where it is installed (the KGP GPU servers); otherwise
    transformers, in bf16 on a GPU with >= 22 GB and in 4-bit NF4 below that (e.g. a Colab T4).
    On Colab this also installs the packages Colab lacks and logs in to Hugging Face (the Llama
    licence needs an HF_TOKEN secret)."""
    if in_colab():
        # Keep Colab's own torch: the cluster's torch build needs a newer driver than Colab has.
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", *COLAB_PACKAGES], check=True)
    token = get_secret("HF_TOKEN")
    if token and os.environ.get("HF_HUB_OFFLINE") != "1":   # offline (cached weights): no login needed
        from huggingface_hub import login
        login(token=token)
    if backend == "auto":
        try:
            import vllm  # noqa: F401
            backend = "vllm"
        except ImportError:
            backend = "hf"
    settings = {"backend": backend}
    if backend == "hf":
        import torch
        assert torch.cuda.is_available(), "A GPU runtime is needed to run the model"
        gib = torch.cuda.get_device_properties(0).total_memory / 2**30
        settings["quant"] = None if gib >= 22 else "4bit"
    print("model settings:", settings)
    return settings


def models_with_results(task: str, smoke: bool = False) -> list[str]:
    """Models that have saved outputs for `task`, in config order."""
    return [m for m in MODELS if any(results_dir(m, task, smoke).glob("*.jsonl"))]


def show_markdown(text: str) -> None:
    from IPython.display import Markdown, display
    display(Markdown(text))
