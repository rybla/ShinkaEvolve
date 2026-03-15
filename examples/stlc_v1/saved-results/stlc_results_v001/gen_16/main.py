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
    Synthesizes STLC terms with a heavy bias towards redex chains and context-driven variable usage.
    """

    def gen_type(nodes: int) -> Ty:
        if nodes <= 1:
            return rng.choice([("Bool",), ("Int",), ("String",)])
        # High probability of function types to force Lam/App structures
        if rng.random() < 0.75:
            return ("Fun", gen_type(nodes // 2), gen_type(nodes // 2))
        return rng.choice([("Bool",), ("Int",), ("String",)])

    def gen_term(ctx: list[Tuple[str, Ty]], target_ty: Ty, budget: int) -> Tm:
        # 1. Variable Lookup (High Priority for used_vars score)
        matching_vars = [n for n, t in ctx if t == target_ty]
        if matching_vars and (budget <= 2 or rng.random() < 0.45):
            return ("Var", rng.choice(matching_vars))

        # 2. Mandatory Lambda for Function Types
        if target_ty[0] == "Fun":
            arg_ty, ret_ty = target_ty[1], target_ty[2]
            vname = f"v{len(ctx)}"
            return ("Lam", vname, arg_ty, gen_term(ctx + [(vname, arg_ty)], ret_ty, budget - 1))

        # 3. Redex Chain Generation (Boosts applied_lambdas and unique_subterms)
        if budget > 30 and rng.random() < 0.3:
            # Create a double-application redex: ((λv1. λv2. body) arg1) arg2
            a1_ty = rng.choice(ctx)[1] if (ctx and rng.random() < 0.6) else gen_type(1)
            a2_ty = rng.choice(ctx)[1] if (ctx and rng.random() < 0.6) else gen_type(1)
            v1, v2 = f"v{len(ctx)}", f"v{len(ctx)+1}"
            
            body = gen_term(ctx + [(v1, a1_ty), (v2, a2_ty)], target_ty, budget // 3)
            inner_lam = ("Lam", v2, a2_ty, body)
            outer_lam = ("Lam", v1, a1_ty, inner_lam)
            
            arg1 = gen_term(ctx, a1_ty, budget // 6)
            arg2 = gen_term(ctx, a2_ty, budget // 6)
            return ("App", ("App", outer_lam, arg1), arg2)

        # 4. Explicit Redex (Single)
        if budget > 12 and rng.random() < 0.35:
            arg_ty = rng.choice(ctx)[1] if (ctx and rng.random() < 0.5) else gen_type(2)
            vname = f"v{len(ctx)}"
            lam = ("Lam", vname, arg_ty, gen_term(ctx + [(vname, arg_ty)], target_ty, budget // 2))
            arg = gen_term(ctx, arg_ty, budget // 3)
            return ("App", lam, arg)

        # 5. Contextual Application (Use existing function variables)
        callables = [(n, t[1]) for n, t in ctx if t[0] == "Fun" and t[2] == target_ty]
        if callables and budget > 5 and rng.random() < 0.6:
            vname, arg_ty = rng.choice(callables)
            return ("App", ("Var", vname), gen_term(ctx, arg_ty, budget - 2))

        # 6. General Application (Synthesize new function)
        if budget > 8:
            # Prefer an arg_ty that allows us to use a variable from context
            if ctx and rng.random() < 0.7:
                arg_ty = rng.choice(ctx)[1]
            else:
                arg_ty = gen_type(1)
            
            # Allocate more budget to the operator to allow it to be a Lam/App
            return ("App", 
                    gen_term(ctx, ("Fun", arg_ty, target_ty), int(budget * 0.65)), 
                    gen_term(ctx, arg_ty, int(budget * 0.25)))

        # 7. Base Case: Literals
        if target_ty == ("Bool",): return ("Bool", rng.choice([True, False]))
        if target_ty == ("Int",): return ("Int", rng.randint(0, 255))
        if target_ty == ("String",): return ("String", rng.choice(["x", "y", "z"]))
        
        # Safety fallback
        return ("Bool", True)

    # Generate a deep type to ensure the term generator has room to work
    target_type = gen_type(rng.randint(6, 12))
    # High initial budget to maximize tm_sizes_average (target ~30-40)
    generated_term = gen_term([], target_type, 90)
    
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