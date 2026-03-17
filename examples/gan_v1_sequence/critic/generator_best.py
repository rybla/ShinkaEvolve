# EVOLVE-BLOCK-START


def sequence_element(i: int) -> int:
    """
    Calculates the ith element of the sequence using bitwise parity logic.
    """
    # Use population count parity to determine the transformation
    # Keeps values small to minimize large_numbers_penalty
    if bin(i).count('1') % 2 == 0:
        return (i ^ 7) - 4
    else:
        return ~(i & 3)


# EVOLVE-BLOCK-END


import inspect
from typing import List, Tuple
import ast

type RunOutput = Tuple[ast.Module, List[int]]


def run_experiment(n: int) -> RunOutput:
    src = inspect.getsource(sequence_element)
    mod = ast.parse(src)
    return mod, [sequence_element(i) ** 2 for i in range(n)]
