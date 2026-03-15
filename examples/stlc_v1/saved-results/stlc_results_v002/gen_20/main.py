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
    Generate high-complexity STLC terms using dynamic redex-chain scaling.
    """

    def gen_type(max_nodes: int) -> Ty:
        if max_nodes <= 1:
            return rng.choice([("Bool",), ("Int",), ("String",)])
        # High probability for functions to create more binding opportunities
        if rng.random() < 0.75:
            left_size = rng.randint(1, max_nodes - 1)
            right_size = max_nodes - 1 - left_size
            return ("Fun", gen_type(left_size), gen_type(right_size))
        return rng.choice([("Bool",), ("Int",), ("String",)])

    def gen_term(ctx: list[Tuple[str, Ty]], target_ty: Ty, budget: int) -> Tm:
        # 1. Variable Match (High Priority for used_vars metric)
        matching_vars = [name for name, ty in ctx if ty == target_ty]
        if matching_vars and (budget <= 2 or rng.random() < 0.45):
            return ("Var", rng.choice(matching_vars))

        # 2. Deep Redex-Chain Injection (The Power Move)
        # Dynamically scales from 2 to 4 nested redexes based on budget
        if budget > 25 and rng.random() < 0.35:
            chain_len = 2
            if budget > 50: chain_len = 3
            if budget > 75: chain_len = 4
            
            arg_types = []
            for _ in range(chain_len):
                # Heavily prioritize context types to ensure 'App' nodes use existing vars
                if ctx and rng.random() < 0.8:
                    arg_types.append(rng.choice(ctx)[1])
                else:
                    arg_types.append(gen_type(1))
            
            # Context extension
            inner_ctx = list(ctx)
            vnames = []
            for i in range(chain_len):
                vname = f"v{len(ctx) + i}"
                vnames.append(vname)
                inner_ctx.append((vname, arg_types[i]))
            
            # Create nested Lam head: \v1. \v2. ... \vn. body
            body_budget = int(budget * 0.4)
            curr_tm = gen_term(inner_ctx, target_ty, body_budget)
            for i in reversed(range(chain_len)):
                curr_tm = ("Lam", vnames[i], arg_types[i], curr_tm)
            
            # Apply the nested head to generated arguments
            # This creates chain_len applied lambdas in one subtree
            for i in range(chain_len):
                arg_tm = gen_term(ctx, arg_types[i], int(budget * 0.1))
                curr_tm = ("App", curr_tm, arg_tm)
            return curr_tm

        # 3. Callable Context Lookup
        if budget > 5:
            callables = [(n, t[1]) for n, t in ctx if t[0] == "Fun" and t[2] == target_ty]
            if callables and rng.random() < 0.6:
                vname, arg_ty = rng.choice(callables)
                return ("App", ("Var", vname), gen_term(ctx, arg_ty, budget - 2))

        # 4. Mandatory Lambda for Function Types
        if target_ty[0] == "Fun":
            _, arg_ty, ret_ty = target_ty
            var_name = f"v{len(ctx)}"
            return ("Lam", var_name, arg_ty, gen_term(ctx + [(var_name, arg_ty)], ret_ty, budget - 1))

        # 5. Forced Redex (Standard)
        if budget > 12 and rng.random() < 0.3:
            arg_ty = rng.choice(ctx)[1] if ctx and rng.random() < 0.7 else gen_type(1)
            vname = f"v{len(ctx)}"
            lam = ("Lam", vname, arg_ty, gen_term(ctx + [(vname, arg_ty)], target_ty, int(budget * 0.5)))
            arg = gen_term(ctx, arg_ty, int(budget * 0.2))
            return ("App", lam, arg)

        # 6. General Application
        if budget > 3:
            # Pick arg_ty from context to satisfy applied arguments with Vars
            arg_ty = rng.choice(ctx)[1] if ctx and rng.random() < 0.75 else gen_type(1)
            fun_ty = ("Fun", arg_ty, target_ty)
            # Allocation skewed to function to keep it complex enough to become a Lam/App
            return ("App", gen_term(ctx, fun_ty, int(budget * 0.7)), gen_term(ctx, arg_ty, int(budget * 0.2)))

        # 7. Safety / Literal Fallbacks
        if target_ty == ("Bool",): return ("Bool", rng.choice([True, False]))
        if target_ty == ("Int",): return ("Int", 101)
        if target_ty == ("String",): return ("String", "dyn")
        return ("Int", 0)

    # Initial type is large to support complex function depths
    target_type = gen_type(rng.randint(7, 10))
    # Budget is high to allow for the dynamic chains to manifest
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