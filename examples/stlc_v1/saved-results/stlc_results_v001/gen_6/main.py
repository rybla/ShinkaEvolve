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
        if rng.random() < 0.6:
            return ("Fun", gen_type(max_nodes // 2), gen_type(max_nodes // 2))
        return rng.choice([("Bool",), ("Int",), ("String",)])

    def gen_term(ctx: list[Tuple[str, Ty]], target_ty: Ty, budget: int) -> Tm:
        # 1. Try to use a variable from context
        matching_vars = [name for name, ty in ctx if ty == target_ty]
        if matching_vars and (budget < 3 or rng.random() < 0.4):
            return ("Var", rng.choice(matching_vars))

        # 2. If target is function, MUST return Lambda to stay well-typed easily
        if target_ty[0] == "Fun":
            _, arg_ty, ret_ty = target_ty
            var_name = f"v{len(ctx)}"
            return ("Lam", var_name, arg_ty, gen_term(ctx + [(var_name, arg_ty)], ret_ty, budget - 1))

        # 3. Application (Redex preference)
        if budget > 10:
            arg_ty = gen_type(3)
            # 50% chance to apply a fresh lambda (increases applied_lambdas)
            if rng.random() < 0.5:
                v_name = f"v{len(ctx)}"
                op = ("Lam", v_name, arg_ty, gen_term(ctx + [(v_name, arg_ty)], target_ty, budget // 2))
                arg = gen_term(ctx, arg_ty, budget // 2)
                return ("App", op, arg)
            else:
                # Apply a variable that is a function
                callables = [name for name, ty in ctx if ty[0] == "Fun" and ty[2] == target_ty]
                if callables:
                    vname = rng.choice(callables)
                    vty = [ty for n, ty in ctx if n == vname][0]
                    return ("App", ("Var", vname), gen_term(ctx, vty[1], budget - 2))

        # 4. Standard Application
        if budget > 4:
            arg_ty = gen_type(2)
            return ("App", gen_term(ctx, ("Fun", arg_ty, target_ty), budget - 5), gen_term(ctx, arg_ty, 3))

        # 5. Literals
        if target_ty == ("Bool",): return ("Bool", rng.choice([True, False]))
        if target_ty == ("Int",): return ("Int", rng.getrandbits(7))
        if target_ty == ("String",): return ("String", rng.choice(["a", "b", "c"]))

        # Fallback
        return ("Bool", True)

    target_type = gen_type(10)
    generated_term = gen_term([], target_type, 95)
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