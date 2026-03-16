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
    Generates well-typed STLC terms with high structural complexity,
    maximizing redex density and variable usage.
    """

    # Global counter to ensure absolute uniqueness of variable names
    var_id = 0

    def get_next_var() -> str:
        nonlocal var_id
        var_id += 1
        return f"x_{var_id}"

    def gen_type(size_limit: int) -> Ty:
        if size_limit <= 1 or rng.random() < 0.25:
            return rng.choice([("Bool",), ("Int",), ("String",)])
        # Favor building function types
        split = rng.randint(1, max(1, size_limit - 1))
        return ("Fun", gen_type(split), gen_type(size_limit - split - 1))

    def gen_term(target_ty: Ty, ctx: list[Tuple[str, Ty]], budget: int) -> Tm:
        # Filter context for variables that match the required type
        valid_vars = [name for name, t in ctx if t == target_ty]

        # Base Case: Budget exhausted or forced leaf
        if budget <= 1:
            if valid_vars:
                # Quadratic recency bias: favor variables added later to the context
                weights = [(i + 1)**2 for i in range(len(valid_vars))]
                return ("Var", rng.choices(valid_vars, weights=weights, k=1)[0])

            # Type-safe literals
            if target_ty == ("Bool",):
                return ("Bool", rng.choice([True, False]))
            if target_ty == ("Int",):
                return ("Int", rng.randint(-1000, 1000))
            if target_ty == ("String",):
                return ("String", rng.choice(["foo", "bar", "baz", "qux"]))

            # Mandatory Lambda for function types to maintain type validity
            if target_ty[0] == "Fun":
                v = get_next_var()
                return ("Lam", v, target_ty[1], gen_term(target_ty[2], ctx + [(v, target_ty[1])], 0))

            return ("Int", 0)

        # Weighted selection of term constructors
        # Dynamic weighting: Favor structure (App/Lam) at high budgets, Vars at low budgets
        choices, weights = [], []

        if target_ty[0] == "Fun":
            choices.append("lam")
            weights.append(30 if budget > 20 else 15)

        if valid_vars:
            choices.append("var")
            weights.append(40 if budget < 30 else 20)

        if budget > 2:
            choices.append("app")
            weights.append(60 if budget > 30 else 30)

        if not choices or (target_ty[0] != "Fun" and rng.random() < 0.1):
            choices.append("lit")
            weights.append(10)

        mode = rng.choices(choices, weights=weights)[0]

        if mode == "lam":
            v_name = get_next_var()
            return ("Lam", v_name, target_ty[1], gen_term(target_ty[2], ctx + [(v_name, target_ty[1])], budget - 1))

        elif mode == "var":
            v_weights = [(i + 1)**2 for i in range(len(valid_vars))]
            return ("Var", rng.choices(valid_vars, weights=v_weights, k=1)[0])

        elif mode == "app":
            # Context-Aware Synthesis: 80% chance to use a type already in ctx
            if ctx and rng.random() < 0.8:
                arg_ty = rng.choice(ctx)[1]
            else:
                arg_ty = gen_type(rng.randint(1, 2))

            # Redex Injection: Construct (Lam x. body) arg
            # Higher base probability to maximize applied_lambdas
            redex_prob = 0.6 + (budget / 250.0)

            # Asymmetric budget split: 0.7 rule for deeper complexity
            split = int(budget * 0.7)

            if rng.random() < redex_prob and budget > 4:
                v_name = get_next_var()
                # Redex injection forces a context expansion
                body = gen_term(target_ty, ctx + [(v_name, arg_ty)], split)

                # Check for existing variables for the argument side to boost used_vars
                arg_vars = [n for n, t in ctx if t == arg_ty]
                if arg_vars and rng.random() < 0.85:
                    v_weights = [(i + 1)**2 for i in range(len(arg_vars))]
                    arg_tm = ("Var", rng.choices(arg_vars, weights=v_weights, k=1)[0])
                else:
                    arg_tm = gen_term(arg_ty, ctx, budget - split - 1)

                return ("App", ("Lam", v_name, arg_ty, body), arg_tm)
            else:
                # Standard application
                return ("App",
                        gen_term(("Fun", arg_ty, target_ty), ctx, split),
                        gen_term(arg_ty, ctx, budget - split - 1))

        else: # lit
            if target_ty == ("Bool",): return ("Bool", rng.choice([True, False]))
            if target_ty == ("Int",): return ("Int", rng.randint(-9999, 9999))
            return ("String", f"val_{rng.randint(0, 10000)}")

    # Generate sample with maximum allowed complexity
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