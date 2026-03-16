"""
Evaluator for generator
"""

import os
import argparse
import numpy as np
from typing import Tuple, Optional, List, Dict, Any

from shinka.core import run_shinka_eval

from .common import RunOutput
from .critic_best import criticize


def validate(
    run_output: RunOutput,
    atol=0.0,
) -> Tuple[bool, Optional[str]]:
    """
    Validates results based on the output of 'run'.

    Args:
        run_output: output from run.

    Returns:
        (is_valid: bool, error_message: Optional[str])
    """

    raise Exception("Unimplemented")


def get_run_kwargs(run_index: int) -> Dict[str, Any]:
    """Provides keyword arguments for run (none needed)."""

    return {}


def aggregate_metrics(results: List[RunOutput], results_dir: str) -> Dict[str, Any]:
    """
    Aggregates metrics. Assumes num_runs=1.
    Saves extra.npz with detailed information.
    """

    if not results:
        return {"combined_score": 0.0, "error": "No results to aggregate"}

    run_output: RunOutput = results[0]

    public_metrics = {}
    private_metrics = {}

    def combined_score() -> float:
        raise Exception("Unimplemented")

    metrics = {
        "combined_score": combined_score(),
        "public": public_metrics,
        "private": private_metrics,
    }

    extra_file = os.path.join(results_dir, "extra.npz")
    try:
        np.savez(extra_file)
        print(f"Detailed data saved to {extra_file}")
    except Exception as e:
        print(f"Error saving extra.npz: {e}")
        metrics["extra_npz_save_error"] = str(e)  # type: ignore

    return metrics


def main(program_path: str, results_dir: str):
    """Runs the evaluation using shinka.eval."""

    print(f"Evaluating program: {program_path}")
    print(f"Saving results to: {results_dir}")
    os.makedirs(results_dir, exist_ok=True)

    num_experiment_runs = 1

    # Define a nested function to pass results_dir to the aggregator
    def _aggregator_with_context(
        r: List[RunOutput],
    ) -> Dict[str, Any]:
        return aggregate_metrics(r, results_dir)

    metrics, correct, error_msg = run_shinka_eval(
        program_path=program_path,
        results_dir=results_dir,
        experiment_fn_name="run",
        num_runs=num_experiment_runs,
        get_experiment_kwargs=get_run_kwargs,
        validate_fn=validate,
        aggregate_metrics_fn=_aggregator_with_context,
    )

    if correct:
        print("Evaluation and Validation completed successfully.")
    else:
        print(f"Evaluation or Validation failed: {error_msg}")

    print("Metrics:")
    for key, value in metrics.items():
        if isinstance(value, str) and len(value) > 100:
            print(f"  {key}: <string_too_long_to_display>")
        else:
            print(f"  {key}: {value}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="evaluator using shinka.eval")
    parser.add_argument(
        "--program_path",
        type=str,
        default="initial.py",
        help="Path to program to evaluate (must contain 'run')",
    )
    parser.add_argument(
        "--results_dir",
        type=str,
        default="results",
        help="Dir to save results (metrics.json, correct.json, extra.npz)",
    )
    parsed_args = parser.parse_args()
    main(parsed_args.program_path, parsed_args.results_dir)
