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
    Ensures well-typedness and aims for high AST node counts and variable usage.
    """

    def gen_type(size_limit: int) -> Ty:
        if size_limit <= 1 or rng.random() < 0.3:
            return rng.choice([("Bool",), ("Int",), ("String",)])

        # Fun type has 1 (Fun) + left + right nodes.
        left_limit = rng.randint(1, size_limit - 2)
        right_limit = size_limit - 1 - left_limit
        return ("Fun", gen_type(left_limit), gen_type(right_limit))

    def type_size(ty: Ty) -> int:
        if ty[0] == "Fun":
            return 1 + type_size(ty[1]) + type_size(ty[2])
        return 1

    def gen_term(ctx: list[Tuple[str, Ty]], target_ty: Ty, size_limit: int) -> Tm:
        # Try to use a variable from context if it matches target_ty
        valid_vars = [name for name, ty in ctx if ty == target_ty]

        # Base cases: Literals or Variables
        if size_limit <= 1 or (not valid_vars and target_ty[0] == "Fun" and size_limit < 3):
            if valid_vars and (rng.random() < 0.7 or target_ty[0] == "Fun"):
                return ("Var", rng.choice(valid_vars))

            if target_ty == ("Bool",):
                return ("Bool", rng.choice([True, False]))
            if target_ty == ("Int",):
                return ("Int", rng.randint(0, 100))
            if target_ty == ("String",):
                return ("String", rng.choice(["abc", "xyz", "lambda"]))

        # Recursive cases
        choices = []
        if valid_vars:
            choices.append("var")
        if target_ty[0] == "Fun":
            choices.append("lam")
        if size_limit > 3:
            choices.append("app")

        pick = rng.choice(choices) if choices else "lit"

        if pick == "var":
            return ("Var", rng.choice(valid_vars))

        if pick == "lam" and target_ty[0] == "Fun":
            # target_ty is (Fun, A, B)
            var_name = f"v{len(ctx)}"
            inner_tm = gen_term(ctx + [(var_name, target_ty[1])], target_ty[2], size_limit - 1)
            return ("Lam", var_name, target_ty[1], inner_tm)

        if pick == "app":
            # To generate (App f x) where f: A -> target_ty and x: A
            arg_ty = gen_type(3) # Keep arg type small to save budget
            f_ty = ("Fun", arg_ty, target_ty)
            # Split budget: 1 for App node, rest for f and x
            f_limit = (size_limit - 1) // 2
            x_limit = size_limit - 1 - f_limit
            return ("App", gen_term(ctx, f_ty, f_limit), gen_term(ctx, arg_ty, x_limit))

        # Fallback to literal
        return gen_term(ctx, target_ty, 1)

    # Generate a type with max 10 nodes
    target_type = gen_type(10)
    # Generate a term with max 100 nodes
    term = gen_term([], target_type, 100)

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