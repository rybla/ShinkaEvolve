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
    Optimized STLC generator focusing on extreme spine depth and variable reuse.
    """

    def gen_type(budget: int) -> Ty:
        if budget <= 1 or rng.random() < 0.25:
            return rng.choice([("Bool",), ("Int",), ("String",)])
        
        left_b = rng.randint(1, max(1, budget - 1))
        return ("Fun", gen_type(left_b), gen_type(max(1, budget - left_b - 1)))

    def gen_term(target_ty: Ty, ctx: List[Tuple[str, Ty]], budget: int) -> Tm:
        # 1. Base Case / Hard Floor
        # If budget is low, prioritize variables to keep used_vars high
        matches = [name for name, ty in ctx if ty == target_ty]
        
        if budget <= 3:
            if matches and rng.random() < 0.98:
                # Prioritize the most recent variable (shadowing bias)
                return ("Var", matches[-1])
            
            if target_ty[0] == "Bool":
                return ("Bool", rng.choice([True, False]))
            if target_ty[0] == "Int":
                return ("Int", rng.randint(0, 1000) + budget)
            if target_ty[0] == "String":
                # Ensure uniqueness via context length and budget
                return ("String", f"s_{len(ctx)}_{budget}_{rng.getrandbits(10)}")
            
            if target_ty[0] == "Fun":
                var_name = f"v{len(ctx)}"
                return ("Lam", var_name, target_ty[1], gen_term(target_ty[2], ctx + [(var_name, target_ty[1])], 1))

        # 2. Lambda Forcing
        # If the type is a function, we usually want a Lambda to increase applied_lambdas score
        if target_ty[0] == "Fun" and rng.random() < 0.82:
            arg_ty, ret_ty = target_ty[1], target_ty[2]
            var_name = f"v{len(ctx)}"
            return ("Lam", var_name, arg_ty, gen_term(ret_ty, ctx + [(var_name, arg_ty)], budget - 1))

        # 3. Extreme Asymmetric Application
        # Strategy: Pick an arg_ty that ALREADY exists in context to maximize Var reuse.
        if ctx and rng.random() < 0.90:
            arg_ty = rng.choice(ctx)[1]
        else:
            arg_ty = gen_type(1)

        fun_ty = ("Fun", arg_ty, target_ty)
        
        # 92/8 Split: Put almost all budget into the function (left) side.
        # This creates massive left-leaning spines: App (App (App ...))
        split_f = int(budget * 0.92)
        split_x = budget - split_f - 1
        
        return ("App", 
                gen_term(fun_ty, ctx, max(1, split_f)), 
                gen_term(arg_ty, ctx, max(1, split_x)))

    # Start with a moderate type and a very high budget to maximize average size
    target_type = gen_type(6)
    # Budget 280 allows for deep recursion without hitting Python's default limit 
    # while pushing tm_sizes_average toward 80-100.
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