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

    def gen_type(budget: int) -> Ty:
        if budget <= 1:
            return rng.choice([("Bool",), ("Int",), ("String",)])
        if rng.random() < 0.3:
            return rng.choice([("Bool",), ("Int",), ("String",)])

        left_budget = rng.randint(1, budget - 1)
        return ("Fun", gen_type(left_budget), gen_type(budget - left_budget))

    def gen_term(target_ty: Ty, ctx: list[Tuple[str, Ty]], budget: int) -> Tm:
        valid_vars = [name for name, ty in ctx if ty == target_ty]

        # Dynamic Variable Selection: If context is rich, favor variables even at slightly higher budgets
        # to save budget for other branches.
        var_prob = 0.95 if len(ctx) > 5 else 0.7
        if budget <= 3:
            if valid_vars and (rng.random() < var_prob or budget <= 1):
                return ("Var", rng.choice(valid_vars))
            if budget <= 1:
                if target_ty == ("Bool",): return ("Bool", rng.choice([True, False]))
                if target_ty == ("Int",): return ("Int", rng.randint(0, 100))
                return ("String", rng.choice(["a", "b", "c"]))

        # Recursive cases: Prioritize Lambda for Fun types to increase variable depth
        if target_ty[0] == "Fun" and (rng.random() < 0.8 or budget < 10):
            arg_ty, ret_ty = target_ty[1], target_ty[2]
            var_name = f"v{len(ctx)}"
            return ("Lam", var_name, arg_ty, gen_term(ret_ty, ctx + [(var_name, arg_ty)], budget - 1))

        # Generate Application: Invent a small intermediate type
        # We use a very small budget for arg_ty to keep the focus on term size
        arg_ty = gen_type(1)
        fun_ty = ("Fun", arg_ty, target_ty)

        # Asymmetric split: 80% to function side to maximize depth and applied lambdas
        split_f = int(budget * 0.8)
        split_x = budget - split_f - 1
        return ("App", gen_term(fun_ty, ctx, split_f), gen_term(arg_ty, ctx, max(1, split_x)))

    # Target type size ~10 nodes, Term size ~100 nodes
    target_type = gen_type(10)
    term = gen_term(target_type, [], 100)

    return target_type, term


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