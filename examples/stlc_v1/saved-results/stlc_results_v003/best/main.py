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
    STLC generator optimized for extreme term size, variable reuse, 
    and beta-redex density.
    """

    def gen_type(budget: int) -> Ty:
        if budget <= 1 or rng.random() < 0.25:
            return rng.choice([("Bool",), ("Int",), ("String",)])
        b_left = rng.randint(1, max(1, budget - 1))
        return ("Fun", gen_type(b_left), gen_type(max(1, budget - b_left - 1)))

    def gen_term(target_ty: Ty, ctx: List[Tuple[str, Ty]], budget: int) -> Tm:
        # 1. Base Case / Budget Exhaustion
        matches = [name for name, ty in ctx if ty == target_ty]
        
        if budget <= 2:
            if matches and rng.random() < 0.98:
                # Use the most recently bound variable to maximize reuse and shadowing
                return ("Var", matches[-1])
            
            # High-entropy literals for unique sub-term scores
            if target_ty[0] == "Bool": 
                return ("Bool", rng.getrandbits(1) == 1)
            if target_ty[0] == "Int": 
                return ("Int", rng.getrandbits(30))
            if target_ty[0] == "String": 
                return ("String", f"s_{len(ctx)}_{rng.getrandbits(20)}")
            
            if target_ty[0] == "Fun":
                v_name = f"v{len(ctx)}_{rng.getrandbits(12)}"
                return ("Lam", v_name, target_ty[1], gen_term(target_ty[2], ctx + [(v_name, target_ty[1])], 1))

        # 2. Lambda Forcing for Function Types
        if target_ty[0] == "Fun" and rng.random() < 0.92:
            v_name = f"v{len(ctx)}_{rng.getrandbits(12)}"
            return ("Lam", v_name, target_ty[1], gen_term(target_ty[2], ctx + [(v_name, target_ty[1])], budget - 1))

        # 3. Application Strategy
        # With 95% probability, pick a type from context to ensure the argument branch uses a Var
        if ctx and rng.random() < 0.95:
            # Weighting: types in ctx are already inhabitants
            arg_ty = rng.choice(ctx)[1]
        else:
            arg_ty = gen_type(1)

        # 95/5 Split: Extreme asymmetry to push term size average > 100
        split_f = int(budget * 0.95)
        split_x = budget - split_f - 1
        
        # 4. Beta-Redex Injection
        # Force the function side to be a Lambda to maximize applied_lambdas_proportions
        if budget > 40 and rng.random() < 0.35:
            v_name = f"v{len(ctx)}_{rng.getrandbits(12)}"
            # Construct a lambda that returns the target type
            fun_tm = ("Lam", v_name, arg_ty, gen_term(target_ty, ctx + [(v_name, arg_ty)], split_f - 1))
            return ("App", fun_tm, gen_term(arg_ty, ctx, max(1, split_x)))

        # Standard Application
        fun_ty = ("Fun", arg_ty, target_ty)
        return ("App", 
                gen_term(fun_ty, ctx, max(1, split_f)), 
                gen_term(arg_ty, ctx, max(1, split_x)))

    # Use a high initial budget to satisfy the 100+ node requirement
    target_type = gen_type(rng.randint(6, 10))
    term = gen_term(target_type, [], 500)

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