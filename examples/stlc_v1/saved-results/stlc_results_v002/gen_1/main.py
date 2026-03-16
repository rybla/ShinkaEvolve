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
def generate_sample(rng: random.Random, depth=10) -> Tuple[Ty, Tm]:
    """
    Generate a sample type and term using a random seed.
    """
    # Generate type with depth control
    ty = generate_type(rng, depth)
    # Generate term with depth control and empty context
    tm = generate_term(rng, depth, [], ty)
    return (ty, tm)

def generate_type(rng: random.Random, depth: int) -> Ty:
    """Generate a type with controlled depth."""
    if depth <= 0:
        # Base types only when depth is exhausted
        return generate_base_type(rng)
    
    # At higher depths, favor function types to build complexity
    if rng.random() < 0.7:
        arg_ty = generate_base_type(rng)
        ret_ty = generate_type(rng, depth - 1)
        return ("Fun", arg_ty, ret_ty)
    
    return generate_base_type(rng)

def generate_base_type(rng: random.Random) -> Ty:
    """Generate a base type."""
    i = rng.randrange(0, 3)
    if i == 0:
        return ("Bool",)
    elif i == 1:
        return ("Int",)
    else:
        return ("String",)

def generate_term(rng: random.Random, depth: int, context: List[Tuple[str, Ty]], target_ty: Ty) -> Tm:
    """Generate a term with controlled depth, respecting the target type."""
    if depth <= 0:
        # At depth 0, generate literals or variables
        return generate_literal_or_var(rng, context, target_ty)
    
    # Decide between lambda, application, or literal
    if isinstance(target_ty, tuple) and target_ty[0] == "Fun":
        # For function types, generate lambda or application
        if rng.random() < 0.5:
            return generate_lambda(rng, depth, context, target_ty)
        else:
            return generate_application(rng, depth, context, target_ty)
    
    # For base types, generate literal or variable
    return generate_literal_or_var(rng, context, target_ty)

def generate_literal_or_var(rng: random.Random, context: List[Tuple[str, Ty]], ty: Ty) -> Tm:
    """Generate a literal or variable."""
    if context and rng.random() < 0.3:
        # Use a variable from context
        var_name, var_ty = rng.choice(context)
        if var_ty == ty:
            return ("Var", var_name)
    
    # Generate a literal matching the type
    if ty == ("Bool",):
        return ("Bool", rng.choice([True, False]))
    elif ty == ("Int",):
        return ("Int", rng.randint(0, 100))
    else:
        return ("String", rng.choice(["hello", "world", "test"]))

def generate_lambda(rng: random.Random, depth: int, context: List[Tuple[str, Ty]], fun_ty: Ty) -> Tm:
    """Generate a lambda term."""
    arg_name = f"x{rng.randint(0, 1000)}"
    arg_ty = fun_ty[1]
    body_ty = fun_ty[2]
    
    # Add argument to context for body generation
    new_context = context + [(arg_name, arg_ty)]
    body = generate_term(rng, depth - 1, new_context, body_ty)
    
    return ("Lam", arg_name, arg_ty, body)

def generate_application(rng: random.Random, depth: int, context: List[Tuple[str, Ty]], target_ty: Ty) -> Tm:
    """Generate an application term."""
    # Generate a function to apply
    fun_ty = ("Fun", generate_base_type(rng), target_ty)
    fun = generate_term(rng, depth - 1, context, fun_ty)
    
    # Generate an argument
    arg_ty = fun_ty[1]
    arg = generate_term(rng, depth - 1, context, arg_ty)
    
    return ("App", fun, arg)
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
