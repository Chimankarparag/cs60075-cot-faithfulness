"""Argument parsing shared by the task scripts."""
from __future__ import annotations

import argparse

from common.config import DATASETS, DEFAULT_DATASET, DEFAULT_MODEL, MODELS, SEED
from common.model import add_model_args


def base_parser(description: str, needs_model: bool = True) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    # The project uses a single dataset (BBH logical deduction); the flag is kept so that
    # commands read the same as before and results stay under results/<task>/bbh/.
    parser.add_argument("--dataset", default=DEFAULT_DATASET, choices=sorted(DATASETS))
    parser.add_argument("--n-limit", type=int, default=None,
                        help="use only the first N eval items (smoke test; results go to results/smoke/)")
    # --model and --seed are read by common/config.py when it is imported (see _run_choice);
    # they are declared here as well so that --help lists them and bad values are rejected.
    parser.add_argument("--model", default=DEFAULT_MODEL, choices=sorted(MODELS),
                        help="model to run; non-default models write to results/models/<model>/")
    parser.add_argument("--seed", type=int, default=SEED,
                        help="generation seed (default 20; the project uses 20, 30, 40); seeds other than 20 "
                             "write to .../seed_<N>/")
    if needs_model:
        add_model_args(parser)
    return parser
