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
    
    # Probabilistic base case termination
    if depth <= 0 or (not bound_vars and rng.random() < 0.5):
        i = rng.randrange(0, 3)
        if i == 0:
            return (("Bool",), ("Bool", rng.choice([True, False])))
        elif i == 1:
            return (("Int",), ("Int", rng.randint(0, 100)))
        else:
            return (("String",), ("String", rng.choice(["hello", "world", "test"])))
    
    # With some probability, return a bound variable
    if bound_vars and rng.random() < 0.35:
        var_name, var_type = rng.choice(bound_vars)
        return (var_type, ("Var", var_name))
    
    i = rng.randrange(0, 5)
    
    if i == 0:
        # Boolean literal
        return (("Bool",), ("Bool", rng.choice([True, False])))
    elif i == 1:
        # Integer literal
        return (("Int",), ("Int", rng.randint(0, 100)))
    elif i == 2:
        # String literal
        return (("String",), ("String", rng.choice(["hello", "world", "test"])))
    elif i == 3:
        # Lambda with unique variable name
        var_name = f"x{rng.randint(0, 100)}"
        var_type = ("Int",)
        inner_ty, inner_tm = generate_sample(rng, depth - 1, bound_vars + [(var_name, var_type)])
        return (
            ("Fun", var_type, inner_ty),
            ("Lam", var_name, var_type, inner_tm)
        )
    else:
        # Application with type checking
        func_ty, func_tm = generate_sample(rng, depth - 1, bound_vars)
        arg_ty, arg_tm = generate_sample(rng, depth - 1, bound_vars)
        
        # Type-safe application: only apply if func is a function type
        if func_ty[0] == "Fun":
            return_type = func_ty[2]
            return (return_type, ("App", func_tm, arg_tm))
        else:
            # Fallback: return the argument if func is not a function
            return (arg_ty, arg_tm)
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
