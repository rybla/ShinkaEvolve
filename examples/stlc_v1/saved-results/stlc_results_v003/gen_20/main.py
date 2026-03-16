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
        # Variable selection: filter context for matching types
        matches = [name for name, ty in ctx if ty == target_ty]

        # Base cases: Hard floor or high-probability variable selection
        if budget <= 2:
            if matches and rng.random() < 0.95:
                return ("Var", rng.choice(matches))

            if target_ty[0] == "Bool":
                return ("Bool", rng.random() > 0.5)
            if target_ty[0] == "Int":
                return ("Int", rng.randint(0, 1000) + budget)
            if target_ty[0] == "String":
                return ("String", f"s_{len(ctx)}_{budget}")

            # If target is Fun but budget exhausted, must return a valid Lam
            if target_ty[0] == "Fun":
                v = f"v{len(ctx)}"
                return ("Lam", v, target_ty[1], gen_term(target_ty[2], ctx + [(v, target_ty[1])], 1))

        # Lambda Forcing: High probability if target is FunTy
        if target_ty[0] == "Fun" and rng.random() < 0.8:
            arg_ty, ret_ty = target_ty[1], target_ty[2]
            var_name = f"v{len(ctx)}"
            return ("Lam", var_name, arg_ty, gen_term(ret_ty, ctx + [(var_name, arg_ty)], budget - 1))

        # Application: Context-aware intermediate type selection
        # 60% chance to pick an argument type from context to maximize Var reuse
        if ctx and rng.random() < 0.6:
            arg_ty = rng.choice(ctx)[1]
        else:
            arg_ty = gen_type(1)

        fun_ty = ("Fun", arg_ty, target_ty)

        # 75/25 Asymmetric split for deep left-heavy application spines
        split_f = int(budget * 0.75)
        split_x = budget - split_f - 1

        return ("App",
                gen_term(fun_ty, ctx, max(1, split_f)),
                gen_term(arg_ty, ctx, max(1, split_x)))

    # Use higher initial budget for deeper ASTs
    target_type = gen_type(rng.randint(2, 6))
    term = gen_term(target_type, [], 120)

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