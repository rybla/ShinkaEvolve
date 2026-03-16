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
    Synthesizes STLC terms with a focus on deep function nesting and 
    frequent variable re-use through exponential recency bias.
    """
    var_counter = 0

    def get_unique_name(prefix: str, depth: int) -> str:
        nonlocal var_counter
        var_counter += 1
        return f"{prefix}_{depth}_{var_counter}_{rng.randint(0, 99)}"

    def gen_type(nodes: int) -> Ty:
        # Increase average type size by slowing down the base-case transition
        if nodes <= 1:
            return rng.choice([("Bool",), ("Int",), ("String",)])
        
        # 80% chance to build a function if budget allows
        if rng.random() < 0.85:
            left = rng.randint(1, nodes - 1)
            return ("Fun", gen_type(left), gen_type(nodes - left))
        return rng.choice([("Bool",), ("Int",), ("String",)])

    def gen_term(ty: Ty, ctx: List[Tuple[str, Ty]], budget: int) -> Tm:
        valid_vars = [name for name, t in ctx if t == ty]

        # Base case logic
        if budget <= 0:
            if valid_vars:
                # Exponential weight to favor the most recent variable
                weights = [4**i for i in range(len(valid_vars))]
                return ("Var", rng.choices(valid_vars, weights=weights, k=1)[0])
            
            if ty[0] == "Fun":
                v = get_unique_name("y", len(ctx))
                return ("Lam", v, ty[1], gen_term(ty[2], ctx + [(v, ty[1])], 0))
            
            if ty == ("Bool",): return ("Bool", rng.choice([True, False]))
            if ty == ("Int",): return ("Int", rng.randint(-5, 5))
            return ("String", "leaf")

        # Distribution tailored to maximize metrics
        # App/Redex (65), Lam (30), Var (40 if available)
        choices, weights = [], []
        if ty[0] == "Fun":
            choices.append("lam"); weights.append(35)
        if valid_vars:
            choices.append("var"); weights.append(45)
        if budget > 2:
            choices.append("app"); weights.append(70)
        
        if not choices:
            choices.append("lit"); weights.append(10)

        mode = rng.choices(choices, weights=weights)[0]

        if mode == "lam":
            v_name = get_unique_name("x", len(ctx))
            return ("Lam", v_name, ty[1], gen_term(ty[2], ctx + [(v_name, ty[1])], budget - 1))

        if mode == "var":
            weights = [4**i for i in range(len(valid_vars))]
            return ("Var", rng.choices(valid_vars, weights=weights, k=1)[0])

        if mode == "app":
            # Decide on an argument type. 90% bias to types already present.
            if ctx and rng.random() < 0.90:
                arg_ty = rng.choice(ctx)[1]
            else:
                arg_ty = gen_type(rng.randint(1, 4))

            # Budget injection for complexity
            # Use 0.8 split for function-type branches to trigger nesting
            split_ratio = 0.8 if ty[0] == "Fun" else 0.7
            split = int(budget * split_ratio)

            # Redex Injection (Forcing Applied Lambdas)
            # P is high (0.65 to 0.85) based on budget
            red_p = 0.65 + (budget / 200.0)
            if rng.random() < red_p and budget > 5:
                v_name = get_unique_name("r", len(ctx))
                f_tm = ("Lam", v_name, arg_ty, gen_term(ty, ctx + [(v_name, arg_ty)], split))
                
                # Force variable usage in arguments to satisfy used_vars metric
                arg_vars = [n for n, t in ctx if t == arg_ty]
                if arg_vars and rng.random() < 0.95:
                    a_weights = [4**i for i in range(len(arg_vars))]
                    a_tm = ("Var", rng.choices(arg_vars, weights=a_weights, k=1)[0])
                else:
                    a_tm = gen_term(arg_ty, ctx, budget - split - 1)
                return ("App", f_tm, a_tm)
            else:
                # Standard application
                return ("App",
                        gen_term(("Fun", arg_ty, ty), ctx, split),
                        gen_term(arg_ty, ctx, budget - split - 1))

        # Literal fallback
        if ty == ("Bool",): return ("Bool", rng.choice([True, False]))
        if ty == ("Int",): return ("Int", rng.randint(-100, 100))
        return ("String", f"v_{rng.randint(0, 999)}")

    # Aim for target complexity: Type size ~8, Term size ~100
    root_ty = gen_type(8)
    root_tm = gen_term(root_ty, [], 100)
    return root_ty, root_tm

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