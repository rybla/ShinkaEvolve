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
    Generates a simply-typed lambda term using a greedy redex-injection strategy
    to maximize applied lambdas and variable usage.
    """

    def gen_type(depth: int) -> Ty:
        if depth <= 1 or rng.random() > 0.7:
            return rng.choice([("Bool",), ("Int",), ("String",)])
        return ("Fun", gen_type(depth - 1), gen_type(depth - 1))

    def gen_term(ctx: list[Tuple[str, Ty]], target_ty: Ty, budget: int) -> Tm:
        # 1. Mandatory Lambda for Function Types
        if target_ty[0] == "Fun":
            arg_ty, ret_ty = target_ty[1], target_ty[2]
            var_name = f"x{len(ctx)}"
            return ("Lam", var_name, arg_ty, gen_term(ctx + [(var_name, arg_ty)], ret_ty, budget - 1))

        # 2. High-Value Redex Injection (Applied Lambdas)
        # We wrap the current goal in a lambda and apply it immediately.
        if budget > 10 and rng.random() < 0.5:
            arg_ty = gen_type(rng.randint(1, 2))
            var_name = f"x{len(ctx)}"
            # (\x. body_of_target_ty) arg_of_arg_ty
            inner_body = gen_term(ctx + [(var_name, arg_ty)], target_ty, budget // 2)
            argument = gen_term(ctx, arg_ty, budget // 2)
            return ("App", ("Lam", var_name, arg_ty, inner_body), argument)

        # 3. Context Exploitation (Used Vars)
        # Look for a variable that is a function returning our target type
        callables = [(n, t[1]) for n, t in ctx if t[0] == "Fun" and t[2] == target_ty]
        if callables and (budget < 5 or rng.random() < 0.6):
            vname, varg_ty = rng.choice(callables)
            return ("App", ("Var", vname), gen_term(ctx, varg_ty, budget - 1))

        # Look for a direct variable match
        matches = [n for n, t in ctx if t == target_ty]
        if matches and (budget < 3 or rng.random() < 0.5):
            return ("Var", rng.choice(matches))

        # 4. Recursive Application (Structural Complexity)
        if budget > 5:
            arg_ty = gen_type(1)
            return ("App", 
                    gen_term(ctx, ("Fun", arg_ty, target_ty), budget // 2), 
                    gen_term(ctx, arg_ty, budget // 2))

        # 5. Base Case Literals
        if target_ty == ("Bool",):
            return ("Bool", rng.choice([True, False]))
        if target_ty == ("Int",):
            return ("Int", rng.randint(0, 1000))
        if target_ty == ("String",):
            return ("String", rng.choice(["foo", "bar", "baz"]))
        
        # Absolute fallback (should not be reached given logic above)
        return ("Bool", True)

    # Start with a complex type to encourage deep terms
    start_ty = gen_type(rng.randint(3, 6))
    # Initial budget of 70 ensures we stay under 100 nodes while being substantial
    start_tm = gen_term([], start_ty, 70)
    
    return start_ty, start_tm

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