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
def generate_sample(rng: random.Random, depth=10, ctx: list[tuple[str, Ty]] = None) -> Tuple[Ty, Tm]:
    if ctx is None:
        ctx = []
    
    # Base case: when depth is 0, generate simple literals
    if depth <= 0:
        i = rng.randrange(0, 3)
        if i == 0:
            return (("Bool",), ("Bool", True))
        elif i == 1:
            return (("Int",), ("Int", 27))
        else:
            return (("String",), ("String", "hello world"))
    
    # At deeper depths, we can create more complex terms
    i = rng.randrange(0, 5)
    
    if i == 0:
        # Generate a Bool literal
        return (("Bool",), ("Bool", rng.choice([True, False])))
    elif i == 1:
        # Generate an Int literal
        return (("Int",), ("Int", rng.randint(0, 100)))
    elif i == 2:
        # Generate a String literal
        return (("String",), ("String", rng.choice(["hello", "world", "test", "foo", "bar"])))
    elif i == 3 and ctx:
        # Use a variable from context
        var_name, var_ty = rng.choice(ctx)
        return (var_ty, ("Var", var_name))
    elif i == 4:
        # Create a lambda with a variable in scope
        arg_ty = ("Int",)
        # Generate body with the variable in context
        ret_ty, body = generate_sample(rng, depth - 1, ctx + [("x", arg_ty)])
        return (
            ("Fun", arg_ty, ret_ty),
            ("Lam", "x", arg_ty, body)
        )
    else:
        # Default to generating a literal
        return (("Bool",), ("Bool", True))
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
