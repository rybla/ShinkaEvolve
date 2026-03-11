from typing import Literal, Tuple
import random


type Ty = BoolTy | IntTy | StringTy | FunTy
type BoolTy = Tuple[Literal["Bool"]]
type IntTy = Tuple[Literal["Int"]]
type StringTy = Tuple[Literal["String"]]
type FunTy = Tuple[Literal["Fun"], Ty, Ty]


type Tm = LitTm | VarTm | LamTm | AppTm
type LitTm = Tuple[Literal["Bool"], bool] | Tuple[Literal["Int"], int] | Tuple[
    Literal["String"], str
]
type VarTm = Tuple[Literal["Var"], str]
type LamTm = Tuple[Literal["Lam"], str, Ty, Tm]
type AppTm = Tuple[Literal["App"], Tm, Tm]


# EVOLVE-BLOCK-START


def generate_term_and_type(rng: random.Random, depth=10) -> Tuple[Ty, Tm]:
    i = rng.randrange(0, 4 if depth > 0 else 3)

    if i == 0:
        return (("Bool",), ("Bool", True))
    elif i == 1:
        return (("Int",), ("Int", 27))
    elif i == 2:
        return (("String",), ("String", "hello world"))
    else:
        ty, tm = generate_term_and_type(rng)
        return (
            ("Fun", ("Int",), ty),
            ("Lam", "x", ("Int",), tm),
        )


# EVOLVE-BLOCK-END


from lc import check_coverage


# This part remains fixed (not evolved)
def run_fuzzing():
    """Run the fuzzer"""

    size = 100
    rng = random.Random()
    samples = [generate_term_and_type(rng) for _ in range(size)]
    return check_coverage(samples)


if __name__ == "__main__":
    run_fuzzing()
