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
    Guarantees well-typedness and respects size limits.
    """

    def gen_type(nodes_budget: int) -> Ty:
        if nodes_budget <= 1 or rng.random() < 0.3:
            return rng.choice([("Bool",), ("Int",), ("String",)])

        # Split budget for FunTy (1 node for Fun, rest for input/output)
        left_budget = rng.randint(1, nodes_budget - 2)
        right_budget = nodes_budget - 1 - left_budget
        return ("Fun", gen_type(left_budget), gen_type(right_budget))

    def get_ty_size(ty: Ty) -> int:
        if ty[0] == "Fun":
            return 1 + get_ty_size(ty[1]) + get_ty_size(ty[2])
        return 1

    def gen_term(ty: Ty, ctx: list[Tuple[str, Ty]], budget: int) -> Tm:
        # Base cases: Literals or Variables
        candidates = [v_name for v_name, v_ty in ctx if v_ty == ty]

        if budget <= 1 or (not candidates and ty[0] == "Fun" and budget < 3):
            if candidates and (rng.random() < 0.7 or ty[0] == "Fun"):
                return ("Var", rng.choice(candidates))
            if ty == ("Bool",):
                return ("Bool", rng.choice([True, False]))
            if ty == ("Int",):
                return ("Int", rng.getrandbits(7))
            if ty == ("String",):
                return ("String", "s")

        # Recursive cases
        # Priority 1: Lambdas for function types
        if ty[0] == "Fun":
            arg_ty, ret_ty = ty[1], ty[2]
            var_name = f"v{len(ctx)}"
            new_ctx = ctx + [(var_name, arg_ty)]
            return ("Lam", var_name, arg_ty, gen_term(ret_ty, new_ctx, budget - 1))

        # Priority 2: Applications to increase size and use variables
        if budget > 3:
            # Randomly pick an intermediate type for application
            mid_ty = gen_type(min(3, (budget // 4)))
            fun_ty = ("Fun", mid_ty, ty)
            # Split budget: App node (1), function (2/3), argument (1/3)
            arg_budget = max(1, budget // 3)
            fun_budget = budget - 1 - arg_budget
            return ("App", gen_term(fun_ty, ctx, fun_budget), gen_term(mid_ty, ctx, arg_budget))

        # Fallback to literal
        if ty == ("Bool",): return ("Bool", True)
        if ty == ("Int",): return ("Int", 1)
        return ("String", "")

    # Main Generation Logic
    # 10 nodes for type is max allowed
    target_ty = gen_type(10)
    # 100 nodes for term is max allowed
    term = gen_term(target_ty, [], 100)

    return target_ty, term


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