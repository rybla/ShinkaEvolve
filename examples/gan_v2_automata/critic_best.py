"""
Generate an initial grid for a cellular automata.
"""

import math
from typing import List


type Cell = float
type Grid = List[List[Cell]]


# EVOLVE-BLOCK-START

def generate_initial_grid(grid_size: int) -> Grid:
    """
    Generates a checkerboard pattern of 0.4000000000000001 and -0.4000000000000001.
    
    1. Standard Deviation: A grid of X and -X has a standard deviation of exactly |X|.
       We use 0.4000000000000001 to strictly satisfy the >= 0.4 requirement.
    2. Velocity Minimization: Smaller values result in smaller inputs to the 
       sine-based update rule, leading to lower velocity.
    3. Period Minimization: The checkerboard pattern ensures that neighborhood 
       averages are small (e.g., (val - val - val)/3 = -val/3), which helps the 
       system converge to a fixed point (Period 1) quickly under the given 
       irrational parameters.
    """
    val = 0.4000000000000001
    grid = []
    for i in range(grid_size):
        row = []
        for j in range(grid_size):
            # Checkerboard pattern to maximize local cancellation
            if (i + j) % 2 == 0:
                row.append(val)
            else:
                row.append(-val)
        grid.append(row)
    return grid

# EVOLVE-BLOCK-END


type RunOutput = Grid


def run_experiment(grid_size: int) -> RunOutput:
    return generate_initial_grid(grid_size)
