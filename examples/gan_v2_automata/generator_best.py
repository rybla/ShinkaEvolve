"""
Design the ruleset for a new cellular automata.
"""

# EVOLVE-BLOCK-START

import math

# Using prime-based irrational numbers and large coefficients to maximize 
# the sensitivity of the sine expansion and avoid early synchronization.
# These values are chosen to create high spatial frequency sensitivity.

cx = 7.1415926535  # High-amplitude scale for horizontal phase
cy = 5.3180339887  # High-amplitude scale for vertical phase
r = 2.7182818284   # Exponential growth factor for right-neighbor influence
u = 3.1415926535   # Pi-based scale for up-neighbor influence
l = 1.7320508075   # Root 3 for left-neighbor influence
d = 2.2360679775   # Root 5 for down-neighbor influence (prevents symmetry with l)

# EVOLVE-BLOCK-END

params = {
    "cx": cx,
    "cy": cy,
    "r": r,
    "u": u,
    "l": l,
    "d": d,
}

from typing import Dict

type RunOutput = Dict


def run_experiment() -> RunOutput:
    return params
