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
    Generates well-typed STLC terms optimized for size, uniqueness, and variable reuse.
    """

    def gen_type(budget: int) -> Ty:
        if budget <= 1 or rng.random() < 0.25:
            return rng.choice([("Bool",), ("Int",), ("String",)])
        
        b_left = rng.randint(1, max(1, budget - 1))
        return ("Fun", gen_type(b_left), gen_type(max(1, budget - b_left - 1)))

    def gen_term(target_ty: Ty, ctx: List[Tuple[str, Ty]], budget: int) -> Tm:
        # 1. Variable Selection (Shadowing-Biased)
        matches = [name for name, ty in ctx if ty == target_ty]

        # Hard Floor Logic
        if budget <= 3:
            if matches and rng.random() < 0.96:
                # Prioritize the most recently bound variable
                return ("Var", matches[-1])
            
            # Unique Literal Generation to maintain uniqueness metrics
            if target_ty[0] == "Bool":
                return ("Bool", rng.choice([True, False]))
            if target_ty[0] == "Int":
                return ("Int", rng.randint(0, 10**8))
            if target_ty[0] == "String":
                # Use context length and budget to ensure string uniqueness
                return ("String", f"s_{len(ctx)}_{budget}_{rng.randint(0, 1000)}")
            
            if target_ty[0] == "Fun":
                v_name = f"v{len(ctx)}"
                return ("Lam", v_name, target_ty[1], gen_term(target_ty[2], ctx + [(v_name, target_ty[1])], 1))

        # 2. High-Density Lambda Forcing
        if target_ty[0] == "Fun" and rng.random() < 0.90:
            arg_ty, ret_ty = target_ty[1], target_ty[2]
            v_name = f"v{len(ctx)}"
            return ("Lam", v_name, arg_ty, gen_term(ret_ty, ctx + [(v_name, arg_ty)], budget - 1))

        # 3. Popularity-Based Context Selection for Applications
        # This maximizes the chance that the argument branch can reuse a variable.
        if ctx and rng.random() < 0.85:
            # Pick a type already present in the context
            arg_ty = rng.choice([t for _, t in ctx])
        else:
            arg_ty = gen_type(1)

        fun_ty = ("Fun", arg_ty, target_ty)
        
        # 92/8 Asymmetric Spine Split
        # Allocating more budget to the function side creates deeper terms.
        split_f = int(budget * 0.92)
        split_x = budget - split_f - 1
        
        return ("App", 
                gen_term(fun_ty, ctx, max(1, split_f)), 
                gen_term(arg_ty, ctx, max(1, split_x)))

    # Target type size 5-10 provides enough complexity for interesting terms
    target_type = gen_type(rng.randint(5, 10))
    
    # High initial budget to push towards the 100-node limit
    term = gen_term(target_type, [], 280)

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