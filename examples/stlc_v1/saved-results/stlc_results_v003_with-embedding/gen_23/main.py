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
    Generates complex STLC terms using double-redex injection and cubic recency bias.
    """
    var_counter = 0

    def get_name(prefix: str) -> str:
        nonlocal var_counter
        var_counter += 1
        return f"{prefix}_{var_counter}_{rng.randint(0, 9999)}"

    def gen_type(size_limit: int) -> Ty:
        # Bias towards function types to enable lambda structures
        if size_limit <= 1 or rng.random() < 0.1:
            return rng.choice([("Bool",), ("Int",), ("String",)])
        split = rng.randint(1, max(1, size_limit - 1))
        return ("Fun", gen_type(split), gen_type(size_limit - split - 1))

    def gen_term(target_ty: Ty, ctx: List[Tuple[str, Ty]], budget: int) -> Tm:
        valid_vars = [name for name, t in ctx if t == target_ty]

        # Terminal case logic
        if budget <= 1:
            if valid_vars:
                # Cubic bias for extreme local variable usage
                weights = [(i + 1)**3 for i in range(len(valid_vars))]
                return ("Var", rng.choices(valid_vars, weights=weights, k=1)[0])
            
            if target_ty[0] == "Fun":
                v = get_name("v")
                return ("Lam", v, target_ty[1], gen_term(target_ty[2], ctx + [(v, target_ty[1])], 0))
            
            if target_ty == ("Bool",): return ("Bool", rng.choice([True, False]))
            if target_ty == ("Int",): return ("Int", rng.randint(-100, 100))
            return ("String", "leaf")

        # Weighted weights to favor App and Lam heavily for metric scores
        choices, weights = [], []
        if target_ty[0] == "Fun":
            choices.append("lam"); weights.append(35)
        if valid_vars:
            choices.append("var"); weights.append(35)
        if budget > 2:
            choices.append("app"); weights.append(75)
        
        if not choices or rng.random() < 0.05:
            choices.append("lit"); weights.append(5)

        mode = rng.choices(choices, weights=weights)[0]

        if mode == "lam":
            v = get_name("x")
            return ("Lam", v, target_ty[1], gen_term(target_ty[2], ctx + [(v, target_ty[1])], budget - 1))

        elif mode == "var":
            v_weights = [(i + 1)**3 for i in range(len(valid_vars))]
            return ("Var", rng.choices(valid_vars, weights=v_weights, k=1)[0])

        elif mode == "app":
            # Context-Aware Sink: prioritize types we already have
            if ctx and rng.random() < 0.8:
                arg_ty = rng.choice(ctx)[1]
            else:
                arg_ty = gen_type(2)

            # Redex Injection Logic
            redex_p = 0.45 + (budget / 150.0)
            if budget > 8 and rng.random() < 0.15: 
                # Novel: Double-Redex Injection
                # (App (Lam x (App (Lam y body) arg2)) arg1)
                v1, v2 = get_name("r1"), get_name("r2")
                inner_arg_ty = rng.choice(ctx)[1] if ctx else gen_type(1)
                
                inner_lam = ("Lam", v2, inner_arg_ty, gen_term(target_ty, ctx + [(v1, arg_ty), (v2, inner_arg_ty)], budget // 3))
                inner_app = ("App", inner_lam, gen_term(inner_arg_ty, ctx + [(v1, arg_ty)], 1))
                outer_lam = ("Lam", v1, arg_ty, inner_app)
                return ("App", outer_lam, gen_term(arg_ty, ctx, budget // 3))
            
            elif budget > 4 and rng.random() < redex_p:
                # Explicit Redex
                v = get_name("r")
                split = int(budget * 0.75)
                f_tm = ("Lam", v, arg_ty, gen_term(target_ty, ctx + [(v, arg_ty)], split))
                a_tm = gen_term(arg_ty, ctx, budget - split - 1)
                return ("App", f_tm, a_tm)
            else:
                # Standard application
                split = rng.randint(1, budget - 1)
                return ("App", gen_term(("Fun", arg_ty, target_ty), ctx, split), gen_term(arg_ty, ctx, budget - split - 1))

        else: # literal
            if target_ty == ("Bool",): return ("Bool", rng.choice([True, False]))
            if target_ty == ("Int",): return ("Int", rng.randint(-1000, 1000))
            return ("String", f"s_{rng.randint(0, 999)}")

    # Objective: Ty size ~10, Tm size ~100
    final_ty = gen_type(10)
    final_tm = gen_term(final_ty, [], 100)
    return final_ty, final_tm

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