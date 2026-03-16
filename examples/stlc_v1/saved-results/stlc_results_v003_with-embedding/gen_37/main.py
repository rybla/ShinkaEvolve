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
    Generates STLC terms with high redex density and variable usage.
    """
    var_counter = 0

    def get_unique_name(prefix: str) -> str:
        nonlocal var_counter
        var_counter += 1
        return f"{prefix}_{var_counter}_{rng.randint(0, 100)}"

    def gen_type(size_limit: int) -> Ty:
        if size_limit <= 1 or rng.random() < 0.15:
            return rng.choice([("Bool",), ("Int",), ("String",)])
        split = rng.randint(1, max(1, size_limit - 1))
        return ("Fun", gen_type(split), gen_type(size_limit - split - 1))

    def gen_term(ty: Ty, ctx: list[Tuple[str, Ty]], budget: int) -> Tm:
        valid_vars = [name for name, t in ctx if t == ty]

        # Base case: Force variable usage or generate minimal valid term
        if budget <= 1:
            if valid_vars and rng.random() < 0.95:
                # Cubic bias for most recent variables
                weights = [(i + 1)**3 for i in range(len(valid_vars))]
                return ("Var", rng.choices(valid_vars, weights=weights, k=1)[0])

            if ty[0] == "Fun":
                v = get_unique_name("v")
                return ("Lam", v, ty[1], gen_term(ty[2], ctx + [(v, ty[1])], 0))

            if ty == ("Bool",): return ("Bool", rng.choice([True, False]))
            if ty == ("Int",): return ("Int", rng.randint(-100, 100))
            return ("String", rng.choice(["s1", "s2", "s3"]))

        # Weighted constructor selection
        choices, weights = [], []
        if ty[0] == "Fun":
            choices.append("lam"); weights.append(30)
        if valid_vars:
            choices.append("var"); weights.append(40)
        if budget > 2:
            choices.append("app"); weights.append(60)
        if not choices or (ty[0] != "Fun" and rng.random() < 0.1):
            choices.append("lit"); weights.append(10)

        mode = rng.choices(choices, weights=weights)[0]

        if mode == "lam":
            v_name = get_unique_name("x")
            return ("Lam", v_name, ty[1], gen_term(ty[2], ctx + [(v_name, ty[1])], budget - 1))

        elif mode == "var":
            v_weights = [(i + 1)**3 for i in range(len(valid_vars))]
            return ("Var", rng.choices(valid_vars, weights=v_weights, k=1)[0])

        elif mode == "app":
            # Context-Aware Type Selection: Prioritize types already in context
            if ctx and rng.random() < 0.85:
                arg_ty = rng.choice(ctx)[1]
            else:
                arg_ty = gen_type(rng.randint(1, 2))

            # Redex Injection Strategy: Probability scales with budget
            redex_prob = 0.55 + (budget / 150.0)
            split = int(budget * 0.7) # Asymmetric 70/30 split

            if rng.random() < redex_prob and budget > 4:
                v_name = get_unique_name("r")
                # Construct redex: (Lam v. body) arg
                f_tm = ("Lam", v_name, arg_ty, gen_term(ty, ctx + [(v_name, arg_ty)], split))
                # For the argument, try to force a variable usage if possible
                arg_vars = [n for n, t in ctx if t == arg_ty]
                if arg_vars and rng.random() < 0.9:
                    v_weights = [(i + 1)**3 for i in range(len(arg_vars))]
                    a_tm = ("Var", rng.choices(arg_vars, weights=v_weights, k=1)[0])
                else:
                    a_tm = gen_term(arg_ty, ctx, budget - split - 1)
                return ("App", f_tm, a_tm)
            else:
                return ("App",
                        gen_term(("Fun", arg_ty, ty), ctx, split),
                        gen_term(arg_ty, ctx, budget - split - 1))

        else: # lit
            if ty == ("Bool",): return ("Bool", rng.choice([True, False]))
            if ty == ("Int",): return ("Int", rng.randint(-1000, 1000))
            return ("String", f"val_{rng.randint(0, 9999)}")

    # Target: Maximize type size (up to 10) and term size (up to 100)
    target_ty = gen_type(10)
    target_tm = gen_term(target_ty, [], 100)

    return target_ty, target_tm

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