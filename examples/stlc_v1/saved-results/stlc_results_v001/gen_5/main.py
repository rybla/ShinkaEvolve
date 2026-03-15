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
    Generate a sample type and term using a random seed, optimized for 
    size, variable usage, and lambda application.
    """

    def get_ty_size(ty: Ty) -> int:
        if ty[0] in ("Bool", "Int", "String"):
            return 1
        return 1 + get_ty_size(ty[1]) + get_ty_size(ty[2])

    def gen_type(max_nodes: int) -> Ty:
        if max_nodes <= 1:
            return rng.choice([("Bool",), ("Int",), ("String",)])
        
        # High probability of generating function types to increase complexity
        if rng.random() < 0.8:
            # Split budget for left and right sides of Fun
            left_limit = rng.randint(1, max_nodes - 2)
            right_limit = max_nodes - 1 - left_limit
            return ("Fun", gen_type(left_limit), gen_type(right_limit))
        
        return rng.choice([("Bool",), ("Int",), ("String",)])

    def gen_term(ctx: List[Tuple[str, Ty]], target_ty: Ty, budget: int) -> Tm:
        if budget <= 1:
            # Try to find a variable first even at low budget
            matching_vars = [n for n, t in ctx if t == target_ty]
            if matching_vars:
                return ("Var", rng.choice(matching_vars))
            
            if target_ty == ("Bool",): return ("Bool", rng.choice([True, False]))
            if target_ty == ("Int",): return ("Int", rng.randint(0, 1000))
            if target_ty == ("String",): return ("String", "val")
            if target_ty[0] == "Fun":
                # Must return a lambda to satisfy function type
                vname = f"x{len(ctx)}"
                return ("Lam", vname, target_ty[1], gen_term(ctx + [(vname, target_ty[1])], target_ty[2], 0))
            return ("Int", 0)

        # 1. If target is Fun, prioritize Lambda to increase applied_lambdas
        if target_ty[0] == "Fun" and rng.random() < 0.9:
            vname = f"x{len(ctx)}"
            return ("Lam", vname, target_ty[1], gen_term(ctx + [(vname, target_ty[1])], target_ty[2], budget - 1))

        # 2. Try to use a function from the context (Application)
        # This increases used_vars and applied_lambdas
        callables = [(n, t) for n, t in ctx if t[0] == "Fun" and t[2] == target_ty]
        if callables and rng.random() < 0.6:
            vname, vty = rng.choice(callables)
            return ("App", ("Var", vname), gen_term(ctx, vty[1], budget - 2))

        # 3. General Application to increase term size
        if budget > 5 and rng.random() < 0.7:
            # Generate a random argument type
            arg_ty = gen_type(3)
            # Split budget: more to the function side to encourage depth
            op_budget = int(budget * 0.7)
            arg_budget = budget - op_budget - 1
            return ("App", 
                    gen_term(ctx, ("Fun", arg_ty, target_ty), op_budget), 
                    gen_term(ctx, arg_ty, arg_budget))

        # 4. Use a variable if available
        matching_vars = [n for n, t in ctx if t == target_ty]
        if matching_vars and rng.random() < 0.8:
            return ("Var", rng.choice(matching_vars))

        # 5. Fallback to literals
        if target_ty == ("Bool",): return ("Bool", True)
        if target_ty == ("Int",): return ("Int", 42)
        if target_ty == ("String",): return ("String", "str")
        
        # Final safety for Fun types
        vname = f"f{len(ctx)}"
        return ("Lam", vname, ("Int",), ("Int", 1))

    # Generate a type close to the 10 node limit
    target_type = gen_type(10)
    # Use a high budget to maximize term size (limit is 100)
    # We use 90 to leave a small buffer for recursive expansions
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