"""
Generate an initial grid for a cellular automata.
"""

from typing import List


type Cell = float
type Grid = List[List[Cell]]


# EVOLVE-BLOCK-START


def generate_initial_grid(grid_size: int) -> Grid:
    return [[0.1 for j in range(grid_size)] for i in range(grid_size)]


# EVOLVE-BLOCK-END


type RunOutput = Grid


def run_experiment(grid_size: int) -> RunOutput:
    return generate_initial_grid(grid_size)
