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
    Generate a well-typed STLC term using type-directed generation,
    asymmetric budget splitting, and context-aware type selection.
    """

    def gen_type(budget: int) -> Ty:
        if budget <= 1 or rng.random() < 0.3:
            return rng.choice([("Bool",), ("Int",), ("String",)])
        
        # Split budget for nested function types
        left_b = rng.randint(1, max(1, budget - 1))
        return ("Fun", gen_type(left_b), gen_type(max(1, budget - left_b - 1)))

    def gen_term(target_ty: Ty, ctx: List[Tuple[str, Ty]], budget: int) -> Tm:
        # 1. Base Case: Hard floor for recursion
        if budget <= 2:
            # High probability to pick from context if a match exists
            matches = [name for name, ty in ctx if ty == target_ty]
            if matches and rng.random() < 0.95:
                return ("Var", rng.choice(matches))
            
            # Fallback to unique literals
            if target_ty[0] == "Bool":
                return ("Bool", rng.choice([True, False]))
            if target_ty[0] == "Int":
                # Use budget/context to ensure uniqueness
                return ("Int", rng.randint(0, 10000) + len(ctx))
            if target_ty[0] == "String":
                return ("String", f"s_{len(ctx)}_{budget}_{rng.randint(0, 100)}")
            
            # If target is Fun but budget is exhausted, we must still return a valid term
            if target_ty[0] == "Fun":
                var_name = f"v{len(ctx)}"
                return ("Lam", var_name, target_ty[1], gen_term(target_ty[2], ctx + [(var_name, target_ty[1])], 1))

        # 2. Recursive Case: Lambda (Type-Directed)
        # If the target is a function, force a Lambda frequently
        if target_ty[0] == "Fun" and rng.random() < 0.7:
            arg_ty, ret_ty = target_ty[1], target_ty[2]
            var_name = f"v{len(ctx)}"
            return ("Lam", var_name, arg_ty, gen_term(ret_ty, ctx + [(var_name, arg_ty)], budget - 1))

        # 3. Recursive Case: Application
        # Pick an argument type 'A'. Favor types already in context to increase Var usage.
        if ctx and rng.random() < 0.7:
            arg_ty = rng.choice(ctx)[1]
        else:
            arg_ty = gen_type(1) # Keep arg types simple to focus budget on term depth

        fun_ty = ("Fun", arg_ty, target_ty)
        
        # Asymmetric split: 70% to function (left), 30% to argument (right)
        # This creates deep left-leaning trees (App (App (App ...)))
        split_f = int(budget * 0.7)
        split_x = budget - split_f - 1
        
        return ("App", 
                gen_term(fun_ty, ctx, max(1, split_f)), 
                gen_term(arg_ty, ctx, max(1, split_x)))

    # Start with a target type (size ~8) and a large term budget (100)
    target_type = gen_type(8)
    term = gen_term(target_type, [], 100)

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