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
    Generates STLC terms optimized for redex density and variable usage.
    """

    def gen_type(max_nodes: int) -> Ty:
        if max_nodes <= 1:
            return rng.choice([("Bool",), ("Int",), ("String",)])
        # High probability for functions to create more binding opportunities
        if rng.random() < 0.75:
            left_size = rng.randint(1, max_nodes // 2)
            right_size = max_nodes - 1 - left_size
            return ("Fun", gen_type(left_size), gen_type(right_size))
        return rng.choice([("Bool",), ("Int",), ("String",)])

    def gen_term(ctx: list[Tuple[str, Ty]], target_ty: Ty, budget: int) -> Tm:
        # 1. Variable Match (Critical for used_vars metric)
        matching_vars = [name for name, ty in ctx if ty == target_ty]
        if matching_vars and (budget <= 3 or rng.random() < 0.50):
            return ("Var", rng.choice(matching_vars))

        # 2. Immediate Redex Injection (Maximize applied_lambdas)
        # Force a redex where the argument is a variable from the context
        if budget > 15 and rng.random() < 0.45:
            # Pick a type already in context if possible to ensure the 'arg' is a Var
            if ctx and rng.random() < 0.85:
                arg_ty = rng.choice(ctx)[1]
            else:
                arg_ty = gen_type(1)

            vname = f"v{len(ctx)}"
            # The function part of the App is a Lambda
            lam_body = gen_term(ctx + [(vname, arg_ty)], target_ty, int(budget * 0.6))
            lam = ("Lam", vname, arg_ty, lam_body)
            # The argument part is a small term, ideally a Var
            arg = gen_term(ctx, arg_ty, 2)
            return ("App", lam, arg)

        # 3. Callable Context Lookup (Strategic variable usage)
        if budget > 5:
            callables = [(n, t[1]) for n, t in ctx if t[0] == "Fun" and t[2] == target_ty]
            if callables and rng.random() < 0.5:
                vname, arg_ty = rng.choice(callables)
                # Use the variable and recurse for its argument
                return ("App", ("Var", vname), gen_term(ctx, arg_ty, budget - 2))

        # 4. Mandatory Lambda for Function Types (Growth of context)
        if target_ty[0] == "Fun":
            _, arg_ty, ret_ty = target_ty
            var_name = f"v{len(ctx)}"
            return ("Lam", var_name, arg_ty, gen_term(ctx + [(var_name, arg_ty)], ret_ty, budget - 1))

        # 5. General Application (Fallback with redex-favoring budget)
        if budget > 2:
            # Favor context types to keep the tree branching towards existing variables
            arg_ty = rng.choice(ctx)[1] if ctx and rng.random() < 0.8 else gen_type(1)
            fun_ty = ("Fun", arg_ty, target_ty)
            # Skew budget heavily to the left to encourage the function to be a Lam
            return ("App", gen_term(ctx, fun_ty, int(budget * 0.75)), gen_term(ctx, arg_ty, int(budget * 0.15)))

        # 6. Safety Literals
        if target_ty == ("Bool",): return ("Bool", rng.choice([True, False]))
        if target_ty == ("Int",): return ("Int", rng.randint(0, 100))
        if target_ty == ("String",): return ("String", "s")
        # Type safety fallback
        return ("Int", 42)

    # Start with a robust type and budget
    target_type = gen_type(rng.randint(8, 12))
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