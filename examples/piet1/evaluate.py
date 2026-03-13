"""
Evaluator for piet1.
"""

import os
import argparse
import random
import numpy as np
from typing import Tuple, Optional, List, Dict, Any

from piet1 import RunOutput, from_path_to_tuple
from shinka.core import run_shinka_eval


def validate_piet1(
    run_output: RunOutput,
    atol=0.0,
) -> Tuple[bool, Optional[str]]:
    """
    Validates piet1 results based on the output of 'run_piet1'.

    Args:
        run_output: output from run_piet1.

    Returns:
        (is_valid: bool, error_message: Optional[str])
    """

    # produce feedback that helps model generate valid results

    max_errors = 10

    good_paths, bad_paths = run_output
    random.shuffle(bad_paths)

    # metrics

    unique_good_paths_count = len(
        set([from_path_to_tuple(path) for path in good_paths])
    )

    unique_good_ratio = unique_good_paths_count / len(good_paths)

    good_bad_ratio = len(good_paths) / len(bad_paths)

    # messages

    bad_msg = f"Many paths are invalid. The ratio of valid paths to invalid paths is {good_bad_ratio}. Here are some of the error messages resulting from the validity checks:\n{"\n".join([ f"The path {bad_path} is invalid because: {msg}" for bad_path, msg in bad_paths[:max_errors] ])}"
    duplicates_msg = f"There are many duplicate paths. The ratio of unique paths to total paths is {unique_good_ratio}."
    good_msg = f"All paths are valid."
    unique_msg = f"Enough paths are unique."
    perfect_msg = f"Excellent work!"

    # returns

    if len(bad_paths) == 0:
        if unique_good_ratio < 0.7:
            return (
                True,
                good_msg + duplicates_msg,
            )
        else:
            return (
                True,
                good_msg + " " + unique_msg + " " + perfect_msg,
            )
    else:
        return (
            True,
            (bad_msg + " " if unique_good_ratio < 0.5 else "") + duplicates_msg,
        )


def get_piet1_kwargs(run_index: int) -> Dict[str, Any]:
    """Provides keyword arguments for piet1 runs (none needed)."""

    return {}


def aggregate_piet1_metrics(
    results: List[RunOutput], results_dir: str
) -> Dict[str, Any]:
    """
    Aggregates metrics for piet1. Assumes num_runs=1.
    Saves extra.npz with detailed piet1 information.
    """

    if not results:
        return {"combined_score": 0.0, "error": "No results to aggregate"}

    good_paths, bad_paths = results[0]
    unique_good_paths_count = len(
        set([from_path_to_tuple(path) for path in good_paths])
    )

    unique_good_ratio = unique_good_paths_count / len(good_paths)
    good_bad_ratio = len(good_paths) / len(bad_paths)

    public_metrics = {
        "unique_good_ratio": unique_good_ratio,
        "good_bad_ratio": good_bad_ratio,
    }
    private_metrics = {}
    metrics = {
        "combined_score": float(unique_good_paths_count),
        "public": public_metrics,
        "private": private_metrics,
    }

    extra_file = os.path.join(results_dir, "extra.npz")
    try:
        np.savez(
            extra_file,
            # union_functions=list(union_functions),
            # union_labels=list(union_labels),
        )
        print(f"Detailed piet1 data saved to {extra_file}")
    except Exception as e:
        print(f"Error saving extra.npz: {e}")
        metrics["extra_npz_save_error"] = str(e)  # type: ignore

    return metrics


def main(program_path: str, results_dir: str):
    """Runs the piet1 evaluation using shinka.eval."""

    print(f"Evaluating program: {program_path}")
    print(f"Saving results to: {results_dir}")
    os.makedirs(results_dir, exist_ok=True)

    num_experiment_runs = 1

    # Define a nested function to pass results_dir to the aggregator
    def _aggregator_with_context(
        r: List[RunOutput],
    ) -> Dict[str, Any]:
        return aggregate_piet1_metrics(r, results_dir)

    metrics, correct, error_msg = run_shinka_eval(
        program_path=program_path,
        results_dir=results_dir,
        experiment_fn_name="run_piet1",
        num_runs=num_experiment_runs,
        get_experiment_kwargs=get_piet1_kwargs,
        validate_fn=validate_piet1,
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
    parser = argparse.ArgumentParser(description="piet1 evaluator using shinka.eval")
    parser.add_argument(
        "--program_path",
        type=str,
        default="initial.py",
        help="Path to program to evaluate (must contain 'run_piet1')",
    )
    parser.add_argument(
        "--results_dir",
        type=str,
        default="results",
        help="Dir to save results (metrics.json, correct.json, extra.npz)",
    )
    parsed_args = parser.parse_args()
    main(parsed_args.program_path, parsed_args.results_dir)
