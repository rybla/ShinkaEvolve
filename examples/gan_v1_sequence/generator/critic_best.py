# EVOLVE-BLOCK-START


import numpy as np
from typing import Callable, List


def infer_sequence_rule(sequence: List[int]) -> Callable[[int], int]:
    """
    Infers the ith element of the sequence using polynomial fitting.
    Given the observed pattern, a 4th degree polynomial is likely.
    """
    x = np.arange(len(sequence))
    y = np.array(sequence)

    # Fit a 4th degree polynomial as the sequence appears to be (quadratic)^2
    poly_coeffs = np.polyfit(x, y, 4)
    poly_func = np.poly1d(poly_coeffs)

    def rule(i: int):
        if i < len(sequence):
            return sequence[i]
        return int(round(poly_func(i)))

    return rule


# EVOLVE-BLOCK-END

type RunOutput = List[int]


def run_experiment(sequence: List[int], n: int) -> RunOutput:
    rule = infer_sequence_rule(sequence)
    return [rule(i) for i in range(n)]