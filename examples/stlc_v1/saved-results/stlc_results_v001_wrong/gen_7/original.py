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


def generate_sample(rng: random.Random) -> Tuple[Ty, Tm]:
    """
    Generate a sample type and term using a random seed.
    """

    def gen_type(max_nodes: int) -> Ty:
        if max_nodes <= 1:
            return rng.choice([("Bool",), ("Int",), ("String",)])
        if rng.random() < 0.7:  # Favor functions
            left_size = rng.randint(1, max_nodes - 1)
            right_size = max_nodes - 1 - left_size
            return ("Fun", gen_type(left_size), gen_type(right_size))
        return rng.choice([("Bool",), ("Int",), ("String",)])

    def gen_term(ctx: list[Tuple[str, Ty]], target_ty: Ty, budget: int) -> Tm:
        # Try to use a variable from context
        candidates = [name for name, ty in ctx if ty == target_ty]
        if candidates and (budget <= 1 or rng.random() < 0.4):
            return ("Var", rng.choice(candidates))

        if budget <= 1:
            if target_ty == ("Bool",):
                return ("Bool", rng.choice([True, False]))
            if target_ty == ("Int",):
                return ("Int", rng.randint(0, 100))
            if target_ty == ("String",):
                return ("String", "s")
            # If target is Fun and we have no budget, we must return a lambda or we'd fail types
            # but we can usually avoid this by better budget management.
            pass

        # Generate Lambda
        if target_ty[0] == "Fun":
            _, arg_ty, ret_ty = target_ty
            var_name = f"v{len(ctx)}"
            new_ctx = ctx + [(var_name, arg_ty)]
            return ("Lam", var_name, arg_ty, gen_term(new_ctx, ret_ty, budget - 1))

        # Generate Application (increase depth and usage)
        if budget > 3 and rng.random() < 0.6:
            arg_ty = gen_type(3)
            fun_ty = ("Fun", arg_ty, target_ty)
            op = gen_term(ctx, fun_ty, budget // 2)
            arg = gen_term(ctx, arg_ty, budget // 2)
            return ("App", op, arg)

        # Fallback to literals
        if target_ty == ("Bool",):
            return ("Bool", True)
        if target_ty == ("Int",):
            return ("Int", 42)
        if target_ty == ("String",):
            return ("String", "xyz")

        # Type safety fallback for unexpected Fun types
        return ("Lam", "unused", ("Int",), ("Int", 0))

    target_type = gen_type(8)
    # Budget of 60 to stay well within 100 node limit
    generated_term = gen_term([], target_type, 60)
    return target_type, generated_term


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