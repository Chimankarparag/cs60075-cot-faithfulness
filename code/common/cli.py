"""Argument parsing shared by the task scripts."""
from __future__ import annotations

import argparse

from common.config import DATASETS
from common.model import add_model_args


def base_parser(description: str, needs_model: bool = True) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--dataset", required=True, choices=sorted(DATASETS))
    parser.add_argument("--n-limit", type=int, default=None,
                        help="use only the first N eval items (smoke test; results go to results/smoke/)")
    if needs_model:
        add_model_args(parser)
    return parser
