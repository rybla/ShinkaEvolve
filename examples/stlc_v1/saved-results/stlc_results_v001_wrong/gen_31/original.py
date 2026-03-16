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
    Generates STLC terms using dynamic redex chains to maximize applied lambdas and variable usage.
    """

    def gen_type(nodes: int) -> Ty:
        if nodes <= 1:
            return rng.choice([("Bool",), ("Int",), ("String",)])
        # High bias towards functions to increase abstraction depth
        if rng.random() < 0.8:
            return ("Fun", gen_type(1), gen_type(nodes - 1))
        return rng.choice([("Bool",), ("Int",), ("String",)])

    def gen_term(ctx: list[Tuple[str, Ty]], target_ty: Ty, budget: int) -> Tm:
        # 1. Variable Lookup (Used Vars Metric)
        matches = [n for n, t in ctx if t == target_ty]
        if matches and (budget <= 2 or rng.random() < 0.4):
            return ("Var", rng.choice(matches))

        # 2. Dynamic Redex-Chain (The Performance Multiplier)
        # Creates ((\v1...vn. body) arg1 ... argn)
        if budget > 35 and rng.random() < 0.4:
            # Determine chain length based on budget (2 to 5)
            n = 2
            if budget > 50: n = 3
            if budget > 70: n = 4
            if budget > 90: n = 5

            # Pick types for the chain, favoring context to use existing Vars
            arg_types = []
            for _ in range(n):
                if ctx and rng.random() < 0.85:
                    arg_types.append(rng.choice(ctx)[1])
                else:
                    arg_types.append(gen_type(1))

            # Build nested context
            inner_ctx = list(ctx)
            vnames = []
            for i in range(n):
                vname = f"v{len(ctx) + i}"
                vnames.append(vname)
                inner_ctx.append((vname, arg_types[i]))

            # Generate body and wrap in Lambdas
            res = gen_term(inner_ctx, target_ty, int(budget * 0.5))
            for i in reversed(range(n)):
                res = ("Lam", vnames[i], arg_types[i], res)

            # Apply to arguments
            for i in range(n):
                arg_tm = gen_term(ctx, arg_types[i], budget // 12)
                res = ("App", res, arg_tm)
            return res

        # 3. Callable Variable Usage
        if budget > 5 and ctx:
            callables = [(n, t[1]) for n, t in ctx if t[0] == "Fun" and t[2] == target_ty]
            if callables and rng.random() < 0.5:
                vname, arg_ty = rng.choice(callables)
                return ("App", ("Var", vname), gen_term(ctx, arg_ty, budget - 2))

        # 4. Mandatory Abstraction for Function Types
        if target_ty[0] == "Fun":
            _, arg_ty, ret_ty = target_ty
            vname = f"v{len(ctx)}"
            return ("Lam", vname, arg_ty, gen_term(ctx + [(vname, arg_ty)], ret_ty, budget - 1))

        # 5. General Application
        if budget > 3:
            # Favor context types for arguments
            arg_ty = rng.choice(ctx)[1] if (ctx and rng.random() < 0.75) else gen_type(1)
            # Skew budget heavily to the operator to encourage more Apps/Lams there
            return ("App",
                    gen_term(ctx, ("Fun", arg_ty, target_ty), int(budget * 0.8)),
                    gen_term(ctx, arg_ty, int(budget * 0.15)))

        # 6. Leaf Fallbacks
        if target_ty == ("Bool",): return ("Bool", rng.choice([True, False]))
        if target_ty == ("Int",): return ("Int", rng.randint(1, 99))
        if target_ty == ("String",): return ("String", "λ")
        return ("Int", 0)

    # Generate a reasonably complex target type
    target_type = gen_type(rng.randint(7, 10))
    # High budget to allow the dynamic chains to trigger
    term = gen_term([], target_type, 115)
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