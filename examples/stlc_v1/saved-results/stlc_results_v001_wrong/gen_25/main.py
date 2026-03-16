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
    Generate a sample type and term using a random seed.
    """

    def gen_type(max_nodes: int) -> Ty:
        if max_nodes <= 1:
            return rng.choice([("Bool",), ("Int",), ("String",)])
        if rng.random() < 0.75:  # Favor functions
            left_size = rng.randint(1, max_nodes - 1)
            right_size = max_nodes - 1 - left_size
            return ("Fun", gen_type(left_size), gen_type(right_size))
        return rng.choice([("Bool",), ("Int",), ("String",)])

    def gen_term(ctx: list[Tuple[str, Ty]], target_ty: Ty, budget: int) -> Tm:
        # Tier 1: Match variable from context
        matching_vars = [name for name, ty in ctx if ty == target_ty]
        if matching_vars and (budget <= 2 or rng.random() < 0.35):
            return ("Var", rng.choice(matching_vars))

        # Tier 2: Deep Currying
        if budget > 8 and ctx:
            potential_callables = []
            for name, ty in ctx:
                args = []
                curr = ty
                while curr[0] == "Fun":
                    args.append(curr[1])
                    curr = curr[2]
                    if curr == target_ty:
                        potential_callables.append((name, args))
                        break
            
            if potential_callables and rng.random() < 0.5:
                vname, args_needed = rng.choice(potential_callables)
                acc = ("Var", vname)
                arg_budget = max(1, budget // (len(args_needed) + 2))
                for arg_ty in args_needed:
                    acc = ("App", acc, gen_term(ctx, arg_ty, arg_budget))
                return acc

        # Tier 3: Redex-Chain: ((\x. \y. body) arg1) arg2
        if budget > 30 and rng.random() < 0.25:
            # Force high-order redex argument 50% of the time
            a1_ty = gen_type(3) if rng.random() < 0.5 else (rng.choice(ctx)[1] if ctx else gen_type(1))
            a2_ty = rng.choice(ctx)[1] if (ctx and rng.random() < 0.6) else gen_type(1)
            v1, v2 = f"v{len(ctx)}", f"v{len(ctx)+1}"
            
            body_budget = int(budget * 0.5)
            arg_budget = budget // 6
            body = gen_term(ctx + [(v1, a1_ty), (v2, a2_ty)], target_ty, body_budget)
            inner_lam = ("Lam", v2, a2_ty, body)
            outer_lam = ("Lam", v1, a1_ty, inner_lam)
            
            return ("App", ("App", outer_lam, gen_term(ctx, a1_ty, arg_budget)), gen_term(ctx, a2_ty, arg_budget))

        # Tier 4: Explicit Redex
        if budget > 12 and rng.random() < 0.35:
            arg_ty = gen_type(2) if rng.random() < 0.5 else (rng.choice(ctx)[1] if ctx else gen_type(1))
            vname = f"v{len(ctx)}"
            lam = ("Lam", vname, arg_ty, gen_term(ctx + [(vname, arg_ty)], target_ty, int(budget * 0.6)))
            arg = gen_term(ctx, arg_ty, int(budget * 0.2))
            return ("App", lam, arg)

        # Tier 5: Mandatory Lambda for Fun types
        if target_ty[0] == "Fun":
            _, arg_ty, ret_ty = target_ty
            var_name = f"v{len(ctx)}"
            return ("Lam", var_name, arg_ty, gen_term(ctx + [(var_name, arg_ty)], ret_ty, budget - 1))

        # Tier 6: General Application
        if budget > 3:
            if ctx and rng.random() < 0.8:
                arg_ty = rng.choice(ctx)[1]
            else:
                arg_ty = gen_type(rng.randint(1, 2))
            
            fun_ty = ("Fun", arg_ty, target_ty)
            return ("App", 
                    gen_term(ctx, fun_ty, int(budget * 0.7)), 
                    gen_term(ctx, arg_ty, int(budget * 0.2)))

        # Fallbacks (Literals)
        if target_ty == ("Bool",): return ("Bool", rng.choice([True, False]))
        if target_ty == ("Int",): return ("Int", rng.randint(0, 100))
        if target_ty == ("String",): return ("String", "s")
        
        return ("Int", 0)

    target_type = gen_type(rng.randint(7, 10))
    # Budget of 110-120 usually stays within 100-node Python object limit for this depth
    generated_term = gen_term([], target_type, 112)
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