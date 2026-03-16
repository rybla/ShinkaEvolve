# EVOLVE-BLOCK-START


def sequence_element(i: int) -> int:
    """
    Calculates the ith element of the sequence.
    """

    return i


# EVOLVE-BLOCK-END


import inspect
from typing import List, Tuple
import ast

type RunOutput = Tuple[ast.Module, List[int]]


def run_experiment(n: int) -> RunOutput:
    src = inspect.getsource(sequence_element)
    mod = ast.parse(src)
    return mod, [sequence_element(i) for i in range(n)]
