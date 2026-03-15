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
def generate_sample(rng: random.Random, depth=10, bound_vars=None) -> Tuple[Ty, Tm]:
    if bound_vars is None:
        bound_vars = []

    # Base case: generate literals when depth is exhausted or randomly at top level
    if depth <= 0 or (not bound_vars and rng.random() < 0.5):
        i = rng.randrange(0, 3)
        if i == 0:
            return (("Bool",), ("Bool", rng.choice([True, False])))
        elif i == 1:
            return (("Int",), ("Int", rng.randint(0, 100)))
        else:
            return (("String",), ("String", rng.choice(["a", "b", "c", "x", "y", "z"])))

    # When we have bound variables, use them with some probability
    if bound_vars and rng.random() < 0.35:
        var_name, var_type = rng.choice(bound_vars)
        return (var_type, ("Var", var_name))

    # Choose between lambda and application
    i = rng.randrange(0, 2)
    if i == 0 and depth > 1:
        # Create a lambda with a fresh variable
        var_name = f"x{rng.randint(0, 100)}"
        var_type = rng.choice([("Bool",), ("Int",), ("String",)])
        _, body = generate_sample(rng, depth - 1, bound_vars + [(var_name, var_type)])
        return (("Fun", var_type, _), ("Lam", var_name, var_type, body))
    else:
        # Create an application - need type-correct function and argument
        # First generate a function type
        arg_type = rng.choice([("Bool",), ("Int",), ("String",)])
        ret_type = rng.choice([("Bool",), ("Int",), ("String",)])
        func_type = ("Fun", arg_type, ret_type)

        # Generate function term - could be a lambda or variable
        if rng.random() < 0.5 and bound_vars:
            # Use an existing variable of function type
            for var_name, var_type in bound_vars:
                if var_type[0] == "Fun":
                    func_term = ("Var", var_name)
                    break
            else:
                # No function variable available, create a lambda
                func_term = ("Lam", "f", arg_type, generate_sample(rng, depth - 1, bound_vars + [("f", arg_type)])[1])
        else:
            # Create a lambda
            func_term = ("Lam", "f", arg_type, generate_sample(rng, depth - 1, bound_vars + [("f", arg_type)])[1])

        # Generate argument term matching the function's input type
        arg_term = generate_sample(rng, depth - 1, bound_vars)[1]

        return (ret_type, ("App", func_term, arg_term))
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