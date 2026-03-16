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

from typing import Dict

class STLCGenerator:
    def __init__(self, rng: random.Random):
        self.rng = rng
        self.var_counter = 0

    def gen_type(self, budget: int) -> Ty:
        if budget <= 1:
            return self.rng.choice([("Bool",), ("Int",), ("String",)])

        if self.rng.random() < 0.2:
            return self.rng.choice([("Bool",), ("Int",), ("String",)])

        left_budget = self.rng.randint(1, budget - 1)
        right_budget = budget - 1 - left_budget
        return ("Fun", self.gen_type(left_budget), self.gen_type(right_budget))

    def gen_term(self, target_ty: Ty, ctx: Dict[str, Ty], budget: int) -> Tm:
        valid_vars = [name for name, ty in ctx.items() if ty == target_ty]

        if budget <= 1:
            if valid_vars:
                return ("Var", self.rng.choice(valid_vars))
            return self.gen_literal(target_ty)

        # 1. Lambda abstraction (if target is Fun)
        if target_ty[0] == "Fun":
            var_name = f"v{self.var_counter}"
            self.var_counter += 1
            new_ctx = ctx.copy()
            new_ctx[var_name] = target_ty[1]
            # Use most of the budget for the body
            return ("Lam", var_name, target_ty[1], self.gen_term(target_ty[2], new_ctx, budget - 1))

        # 2. Application (to grow size and use variables)
        if budget > 3:
            # To maximize applied_lambdas, we force the left side to be a Lam sometimes
            # or just a general term of function type.
            arg_ty = self.gen_type(self.rng.randint(1, 4))
            fun_ty = ("Fun", arg_ty, target_ty)

            split = self.rng.randint(1, budget - 2)
            left_tm = self.gen_term(fun_ty, ctx, split)
            right_tm = self.gen_term(arg_ty, ctx, budget - 1 - split)
            return ("App", left_tm, right_tm)

        # 3. Variable usage (high priority for leaf nodes)
        if valid_vars and (budget <= 2 or self.rng.random() < 0.5):
            return ("Var", self.rng.choice(valid_vars))

        return self.gen_literal(target_ty)

    def gen_literal(self, ty: Ty) -> LitTm:
        if ty[0] == "Bool":
            return ("Bool", self.rng.choice([True, False]))
        elif ty[0] == "Int":
            return ("Int", self.rng.randint(0, 1000))
        else:
            return ("String", self.rng.choice(["lambda", "type", "logic", "stlc"]))

def generate_sample(rng: random.Random) -> Tuple[Ty, Tm]:
    gen = STLCGenerator(rng)
    # Maximize type size (limit 10)
    target_ty = gen.gen_type(rng.randint(5, 10))
    # Maximize term size (limit 100)
    term = gen.gen_term(target_ty, {}, rng.randint(60, 95))
    return target_ty, term

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