"""
Design the ruleset for a new cellular automata.
"""

# EVOLVE-BLOCK-START

# We use square roots of primes to ensure parameters are incommensurate.
# This prevents the initial checkerboard from settling into a short period.

# c: self-feedback. 
# Using (sqrt(5)-1)/2 (approx 0.618) but scaled to keep dynamics slow.
c = 0.30901699437  

# r: right neighborhood. 
# Using sqrt(2)/3 to provide a strong horizontal shift.
r = 0.47140452079  

# u: up neighborhood. 
# Using -sqrt(3)/6 to break vertical symmetry and induce drift.
u = -0.28867513459 

# l: left neighborhood. 
# Using sqrt(7)/8 to create interference with the right-side influence.
l = 0.33071891388  

# d: down neighborhood. 
# Using -sqrt(11)/20 for a subtle, non-rational vertical counter-drift.
d = -0.16583123951 

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