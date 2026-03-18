"""
Generate an initial grid for a cellular automata.
"""

import math
from typing import List


type Cell = float
type Grid = List[List[Cell]]


# EVOLVE-BLOCK-START


def generate_initial_grid(grid_size: int) -> Grid:
    return [
        [math.sin((i + j) / 32.0) for j in range(grid_size)] for i in range(grid_size)
    ]


# EVOLVE-BLOCK-END


type RunOutput = Grid


def run_experiment(grid_size: int) -> RunOutput:
    return generate_initial_grid(grid_size)
