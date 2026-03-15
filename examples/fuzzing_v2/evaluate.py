"""
Evaluator for fuzzing.
"""

import os
import argparse
import numpy as np
from typing import Tuple, Optional, List, Dict, Any

from lc import RunOutput
from .common import ty_size_max, tm_size_max
from shinka.core import run_shinka_eval


def validate_fuzzing(
    run_output: RunOutput,
    atol=0.0,
) -> Tuple[bool, Optional[str]]:
    """
    Validates fuzzing results based on the output of 'run'.

    Args:
        run_output: output from run.

    Returns:
        (is_valid: bool, error_message: Optional[str])
    """

    # produce feedback that helps model generate valid results

    # TODO: reject badly-typed generations?

    goods, bads = run_output

    if len(bads) == 0:
        return True, "All generations were successful and well-typed."
    else:
        return (
            True,
            """
Some generations raised exceptions during generation, grammar checking, or type checking. These are some examples:
TODO: some example exceptions
""".strip(),
        )


def get_fuzzing_kwargs(run_index: int) -> Dict[str, Any]:
    """Provides keyword arguments for fuzzing runs (none needed)."""

    return {}


def aggregate_fuzzing_metrics(
    results: List[RunOutput], results_dir: str
) -> Dict[str, Any]:
    """
    Aggregates metrics for fuzzing. Assumes num_runs=1.
    Saves extra.npz with detailed fuzzing information.
    """

    if not results:
        return {"combined_score": 0.0, "error": "No results to aggregate"}

    goods, bads = results[0]

    goods_count = len(goods)
    bads_count = len(bads)
    goods_to_bads_ratio = goods_count / bads_count

    # only for goods
    tm_sizes = np.array([good.tm_size() for good in goods])
    tm_sizes_average = np.average(tm_sizes)

    ty_sizes = np.array([good.ty_size() for good in goods])
    ty_sizes_average = np.average(ty_sizes)

    used_vars_proportions = np.array([good.used_vars_proportion() for good in goods])
    used_vars_proportions_average = np.average(used_vars_proportions)

    applied_lambdas_proportions = np.array(
        [good.applied_lambdas_proportion() for good in goods]
    )
    applied_lambdas_proportions_average = np.average(applied_lambdas_proportions)

    unique_subterms_proportions = np.array(
        [good.unique_subterms_proportion() for good in goods]
    )
    unique_subterms_proportions_average = np.average(unique_subterms_proportions)

    public_metrics = {
        "goods_bads_proportion": goods_to_bads_ratio,
        "tm_sizes_average": tm_sizes_average,
        "ty_sizes_average": ty_sizes_average,
        "used_vars_proportions_average": used_vars_proportions_average,
        "applied_lambdas_proportions_average": applied_lambdas_proportions_average,
        "unique_subterms_proportions_average": unique_subterms_proportions_average,
    }
    private_metrics = {}
    metrics = {
        "combined_score": float(
            0.0
            + 10.0 * goods_to_bads_ratio
            + 1.0 * (min(ty_sizes_average, ty_size_max) / ty_size_max)
            + 1.0 * (min(tm_sizes_average, tm_size_max) / tm_size_max)
            + 1.0 * used_vars_proportions_average
            + 1.0 * applied_lambdas_proportions_average
            + 1.0 * unique_subterms_proportions_average
        ),
        "public": public_metrics,
        "private": private_metrics,
    }

    extra_file = os.path.join(results_dir, "extra.npz")
    try:
        np.savez(extra_file)
        print(f"Detailed fuzzing data saved to {extra_file}")
    except Exception as e:
        print(f"Error saving extra.npz: {e}")
        metrics["extra_npz_save_error"] = str(e)  # type: ignore

    return metrics


def main(program_path: str, results_dir: str):
    """Runs the fuzzing evaluation using shinka.eval."""

    print(f"Evaluating program: {program_path}")
    print(f"Saving results to: {results_dir}")
    os.makedirs(results_dir, exist_ok=True)

    num_experiment_runs = 1

    # Define a nested function to pass results_dir to the aggregator
    def _aggregator_with_context(
        r: List[RunOutput],
    ) -> Dict[str, Any]:
        return aggregate_fuzzing_metrics(r, results_dir)

    metrics, correct, error_msg = run_shinka_eval(
        program_path=program_path,
        results_dir=results_dir,
        experiment_fn_name="run",
        num_runs=num_experiment_runs,
        get_experiment_kwargs=get_fuzzing_kwargs,
        validate_fn=validate_fuzzing,
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
    parser = argparse.ArgumentParser(description="Fuzzing evaluator using shinka.eval")
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
