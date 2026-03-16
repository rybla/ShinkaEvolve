# EVOLVE-BLOCK-START


import bisect
from typing import Callable, List


def linear_interpolate(points: List[tuple[int, int]], x: int) -> int:
    if not points:
        raise ValueError("The list of points cannot be empty.")

    x_coords = [p[0] for p in points]

    if x <= x_coords[0]:
        return points[0][1]
    if x >= x_coords[-1]:
        return points[-1][1]

    i = bisect.bisect_right(x_coords, x)

    x1, y1 = points[i - 1]
    x2, y2 = points[i]

    return round(y1 + (x - x1) * (y2 - y1) / (x2 - x1))


def infer_sequence_rule(sequence: List[int]) -> Callable[[int], int]:
    """
    Infers the ith element of the sequence.
    """

    points = list(enumerate(sequence))

    def rule(i: int):
        return linear_interpolate(points, i)

    return rule


# EVOLVE-BLOCK-END

type RunOutput = List[int]


def run_experiment(sequence: List[int], n: int) -> RunOutput:
    rule = infer_sequence_rule(sequence)
    return [rule(i) for i in range(n)]
