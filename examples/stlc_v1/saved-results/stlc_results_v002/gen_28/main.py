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
    Generate a sample type and term using a dynamic redex-chain approach.
    """

    def gen_type(max_nodes: int) -> Ty:
        if max_nodes <= 1:
            return rng.choice([("Bool",), ("Int",), ("String",)])
        if rng.random() < 0.75:  # High bias for functions to force Lam/App
            left_size = rng.randint(1, max(1, max_nodes - 2))
            right_size = max_nodes - 1 - left_size
            return ("Fun", gen_type(left_size), gen_type(right_size))
        return rng.choice([("Bool",), ("Int",), ("String",)])

    def gen_term(ctx: list[Tuple[str, Ty]], target_ty: Ty, budget: int) -> Tm:
        # 1. Variable Match (High Priority)
        matching_vars = [name for name, ty in ctx if ty == target_ty]
        if matching_vars and (budget <= 2 or rng.random() < 0.45):
            return ("Var", rng.choice(matching_vars))

        # 2. Callable Lookup (Medium Priority)
        if budget > 5:
            callables = [(n, t[1]) for n, t in ctx if t[0] == "Fun" and t[2] == target_ty]
            if callables and rng.random() < 0.65:
                vname, arg_ty = rng.choice(callables)
                return ("App", ("Var", vname), gen_term(ctx, arg_ty, budget - 2))

        # 3. Dynamic Redex-Chain (Optimized Strategy)
        # Create a chain of nested lambdas applied to arguments to maximize metrics
        if budget > 35 and rng.random() < 0.35:
            chain_len = rng.randint(2, 3)
            arg_types = []
            for _ in range(chain_len):
                # Prioritize context types to ensure arguments can be 'Var'
                if ctx and rng.random() < 0.8:
                    arg_types.append(rng.choice(ctx)[1])
                else:
                    arg_types.append(gen_type(1))

            # Build the nested Lambda block
            new_ctx = list(ctx)
            names = []
            for i, aty in enumerate(arg_types):
                name = f"v{len(ctx) + i}"
                names.append(name)
                new_ctx.append((name, aty))

            # Body gets a significant portion of budget to allow further recursion
            body = gen_term(new_ctx, target_ty, int(budget * 0.5))

            # Wrap body in Lambdas: Lam v1. (Lam v2. body)
            fun_part = body
            for i in reversed(range(chain_len)):
                fun_part = ("Lam", names[i], arg_types[i], fun_part)

            # Apply the chain to arguments: App(App(Lam_Chain, arg1), arg2)
            res = fun_part
            for i in range(chain_len):
                # Small budget for args to encourage them being 'Var' or literals
                arg_tm = gen_term(ctx, arg_types[i], 2)
                res = ("App", res, arg_tm)
            return res

        # 4. Standard Lambda (Mandatory for Fun types)
        if target_ty[0] == "Fun":
            _, arg_ty, ret_ty = target_ty
            var_name = f"v{len(ctx)}"
            return ("Lam", var_name, arg_ty, gen_term(ctx + [(var_name, arg_ty)], ret_ty, budget - 1))

        # 5. General Application (Budget Splitting)
        if budget > 3:
            # Try to pick an arg_ty that exists in context
            if ctx and rng.random() < 0.8:
                arg_ty = rng.choice(ctx)[1]
            else:
                arg_ty = gen_type(rng.randint(1, 2))

            fun_ty = ("Fun", arg_ty, target_ty)
            # Allocate more budget to the function to encourage it being a Lam or App (Redex)
            return ("App", gen_term(ctx, fun_ty, int(budget * 0.65)), gen_term(ctx, arg_ty, int(budget * 0.25)))

        # 6. Fallbacks (Base Cases)
        if target_ty == ("Bool",):
            return ("Bool", rng.choice([True, False]))
        if target_ty == ("Int",):
            return ("Int", rng.randint(0, 100))
        if target_ty == ("String",):
            return ("String", "xyz")

        # Safety for unexpected type shapes
        return ("Int", 0)

    # Generate a complex target type (7-11 nodes)
    target_type = gen_type(rng.randint(8, 11))
    # High initial budget to maximize term size and complexity
    generated_term = gen_term([], target_type, 115)
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