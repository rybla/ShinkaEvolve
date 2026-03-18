"""
Design the ruleset for a new cellular automata.
"""

# EVOLVE-BLOCK-START

import math


c = 1.61803398875  # Golden ratio
r = math.e - 2.0
u = math.pi - 2.0
l = math.sqrt(3.0) / 2.0
d = math.sqrt(5.0) - 1.0


# EVOLVE-BLOCK-END

params = {
    "c": c,
    "r": r,
    "u": u,
    "l": l,
    "d": d,
}

from typing import Dict

type RunOutput = Dict


def run_experiment() -> RunOutput:
    return params
