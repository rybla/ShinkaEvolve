from typing import Literal, Tuple
import random
import tqdm

"""
`Ty` and `Tm` define the shape of a simply-typed lambda-calculus deeply embedded in Python.

Each value, be it the encoding of a type or a term, is a tuple where the first component of the tuple is the "constructor" and the rest of the components are the arguments. For example, this value encodes the `Bool` type:

    ('Bool',)

As another example, this value encodes the function type from `Bool` to `Bool`, which is often written `Bool -> Bool`:

    ('Fun', ('Bool',), ('Bool',))

As another example, this value encodes the function term, which takes a single `String` input and just returns that input (also known as the identity function):

    ('Lam', 'x', ('String',), ('Var', 'x'))

Note that ALL lambda terms must have a type annotation as the 1st argument, where in the above example the type annotation was the ('String',).

Closely read the above below type aliases to understand the complete structure of this deep embedding of the lambda calculus in Python.
"""

type Ty = BoolTy | IntTy | StringTy | FunTy
type BoolTy = Tuple[Literal["Bool"]]
type IntTy = Tuple[Literal["Int"]]
type StringTy = Tuple[Literal["String"]]
type FunTy = Tuple[Literal["Fun"], Ty, Ty]


type Tm = LitTm | VarTm | LamTm | AppTm
type LitTm = (
    Tuple[Literal["Bool"], bool]
    | Tuple[Literal["Int"], int]
    | Tuple[Literal["String"], str]
)
type VarTm = Tuple[Literal["Var"], str]
type LamTm = Tuple[Literal["Lam"], str, Ty, Tm]
type AppTm = Tuple[Literal["App"], Tm, Tm]


# EVOLVE-BLOCK-START
def generate_sample(rng: random.Random, depth=10, context=None) -> Tuple[Ty, Tm]:
    if context is None:
        context = []

    # At depth 0, only generate literals
    if depth == 0:
        i = rng.randrange(0, 3)
        if i == 0:
            return (("Bool",), ("Bool", True))
        elif i == 1:
            return (("Int",), ("Int", 27))
        else:
            return (("String",), ("String", "hello world"))

    # At depth > 0, choose from literals, Lam, and App
    i = rng.randrange(0, 5)  # 5 options

    if i == 0:
        return (("Bool",), ("Bool", True))
    elif i == 1:
        return (("Int",), ("Int", 27))
    elif i == 2:
        return (("String",), ("String", "hello world"))
    elif i == 3:
        # Generate lambda - always recurse to build more complex terms
        ty, tm = generate_sample(rng, depth - 1, context + ["x"])
        return (("Fun", ("Int",), ty), ("Lam", "x", ("Int",), tm))
    else:
        # Generate application - apply a lambda to an argument
        arg_ty, arg_tm = generate_sample(rng, depth - 1, context)
        func_ty = ("Fun", arg_ty, arg_ty)
        func_tm = ("Lam", "x", arg_ty, ("Var", "x"))
        return (arg_ty, ("App", func_tm, arg_tm))
# EVOLVE-BLOCK-END

# This part remains fixed (not evolved)

import lc


def run() -> lc.RunOutput:
    """Run the analysis"""

    size = 1000
    rng = random.Random()

    return lc.run(
        size=size,
        rng=rng,
        generate_sample=generate_sample,
    )