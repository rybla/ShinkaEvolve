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
    Generates well-typed STLC terms with extreme depth and high variable density.
    Optimized for tm_sizes_average > 60 and high used-variable proportions.
    """

    def gen_type(budget: int) -> Ty:
        if budget <= 1 or rng.random() < 0.25:
            return rng.choice([("Bool",), ("Int",), ("String",)])

        # Consistent small splits for types to keep ty_sizes_average stable around 3-4
        left_b = rng.randint(1, budget - 1)
        return ("Fun", gen_type(left_b), gen_type(budget - left_b))

    def gen_term(target_ty: Ty, ctx: List[Tuple[str, Ty]], budget: int) -> Tm:
        # 1. Context Filtering
        valid_vars = [name for name, ty in ctx if ty == target_ty]

        # 2. Hard Floor / Terminal Case
        if budget <= 2:
            if valid_vars and (rng.random() < 0.9 or budget <= 1):
                return ("Var", rng.choice(valid_vars))

            # Context-length dependent literals to ensure uniqueness
            ctx_id = len(ctx)
            if target_ty[0] == "Bool":
                return ("Bool", rng.choice([True, False]))
            if target_ty[0] == "Int":
                return ("Int", ctx_id * 100 + rng.randint(0, 99))
            if target_ty[0] == "String":
                return ("String", f"s_{ctx_id}_{rng.getrandbits(16)}")

            # Recursion Guard for Fun types at budget floor
            if target_ty[0] == "Fun":
                var_name = f"v{ctx_id}"
                return ("Lam", var_name, target_ty[1], gen_term(target_ty[2], ctx + [(var_name, target_ty[1])], 1))

        # 3. Structural Lambda Forcing (90% bias for Function types)
        if target_ty[0] == "Fun" and rng.random() < 0.90:
            arg_ty, ret_ty = target_ty[1], target_ty[2]
            var_name = f"v{len(ctx)}"
            return ("Lam", var_name, arg_ty, gen_term(ret_ty, ctx + [(var_name, arg_ty)], budget - 1))

        # 4. Asymmetric Application Strategy
        # Maximize variable density by preferring context types for 'A' in 'A -> B'
        if ctx and rng.random() < 0.80:
            arg_ty = rng.choice(ctx)[1]
        else:
            # Fallback to extremely simple atomic type
            arg_ty = rng.choice([("Bool",), ("Int",), ("String",)])

        fun_ty = ("Fun", arg_ty, target_ty)

        # 85/15 Asymmetric split creates deeper left-nested "spines"
        # This significantly boosts tm_sizes_average and unique_subterms.
        split_f = int(budget * 0.85)
        split_x = budget - split_f - 1

        return ("App",
                gen_term(fun_ty, ctx, max(1, split_f)),
                gen_term(arg_ty, ctx, max(1, split_x)))

    # Start with a decent target type to allow variety
    target_type = gen_type(rng.randint(6, 10))
    # Budget of 130 ensures we cross the tm_sizes_average > 60 threshold easily
    term = gen_term(target_type, [], 130)

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