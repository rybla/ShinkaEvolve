"""
Design the ruleset for a new cellular automata.
"""

# EVOLVE-BLOCK-START

import math

# We use square roots of primes to ensure parameters are incommensurate.
# This prevents the initial checkerboard from settling into a short period.
# The goal is to maximize the period by ensuring the phase shifts never align.

# c: self-feedback.
# Using sqrt(2)/10 to provide a stable but irrational self-influence.
c = 0.14142135623

# r: right neighborhood.
# Using sqrt(3)/12 to create horizontal propagation.
r = 0.14433756729

# u: up neighborhood.
# Using -sqrt(5)/11 to break vertical symmetry strongly.
u = -0.20327891707

# l: left neighborhood.
# Using sqrt(7)/13 to interfere with the right-side influence.
l = 0.20351894511

# d: down neighborhood.
# Using -sqrt(11)/17 for a subtle, non-rational vertical counter-drift.
d = -0.19509618943

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