"""Record where and how long a run took: host, GPUs, software versions, wall-clock per stage.

Every task script wraps its work in a RunRecord. On exit it appends one entry to
<results dir>/run_info.json (a list, so resumed or partial runs keep their history):

    {"script": "code/task3/run_task3.py --tp 1", "host": "gpu74.cse.iitkgp",
     "gpus": ["NVIDIA A40"], "cuda_visible_devices": "0", "model": ..., "gen_seed": 20,
     "started": "2026-11-03T15:02:11+05:30", "finished": ..., "seconds": 1234.5,
     "stages": {"sample": 512.3, "early50": 40.1, ...}, "versions": {...}, "status": "ok"}

Stages that are skipped because their output already exists are not timed, so the
numbers measure only the work that run actually did. Runs that only re-score saved files
(no model loaded) are not recorded.
"""
from __future__ import annotations

import json
import os
import platform
import socket
import subprocess
import sys
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from common.config import GEN_SEED, MODEL_ID, MODEL_KEY, MODEL_REVISION


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _gpus() -> list[str]:
    """Names of the GPUs this process can see (respects CUDA_VISIBLE_DEVICES)."""
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=index,name", "--format=csv,noheader"],
                             capture_output=True, text=True, timeout=20).stdout
    except (OSError, subprocess.SubprocessError):
        return []
    names = {}
    for line in out.strip().splitlines():
        idx, name = (x.strip() for x in line.split(",", 1))
        names[idx] = name
    visible = os.environ.get("CUDA_VISIBLE_DEVICES")
    wanted = visible.split(",") if visible else sorted(names)
    return [names.get(i.strip(), f"gpu {i}") for i in wanted if i.strip()]


def _versions() -> dict:
    found = {"python": platform.python_version()}
    for pkg in ("vllm", "torch", "transformers"):
        try:
            found[pkg] = __import__(pkg).__version__
        except Exception:  # not installed (e.g. scoring on a laptop)
            pass
    return found


class RunRecord:
    def __init__(self, out_dir: Path, args=None, enabled: bool = True):
        self.enabled = enabled
        self.path = Path(out_dir) / "run_info.json"
        self.entry = {
            "script": " ".join([os.path.relpath(sys.argv[0])] + sys.argv[1:]),
            "host": socket.gethostname(),
            "gpus": _gpus() if enabled else [],
            "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
            "backend": getattr(args, "backend", None),
            "tensor_parallel": getattr(args, "tp", None),
            "model_key": MODEL_KEY, "model": MODEL_ID, "model_revision": MODEL_REVISION,
            "gen_seed": GEN_SEED,
            "started": _now(), "finished": None, "seconds": None,
            "stages": {}, "status": "running",
        }
        self._t0 = time.time()

    @contextmanager
    def stage(self, name: str):
        start = time.time()
        yield
        self.entry["stages"][name] = round(time.time() - start, 1)
        print(f"[time] {name}: {self.entry['stages'][name]:.0f}s", flush=True)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        if not self.enabled:
            return False
        self.entry["finished"] = _now()
        self.entry["seconds"] = round(time.time() - self._t0, 1)
        self.entry["status"] = "ok" if exc_type is None else f"failed: {exc_type.__name__}"
        self.entry["versions"] = _versions()   # after the run, so lazily imported packages show up
        history = []
        if self.path.exists():
            try:
                history = json.loads(self.path.read_text())
            except json.JSONDecodeError:
                history = []
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(history + [self.entry], indent=2) + "\n")
        return False
