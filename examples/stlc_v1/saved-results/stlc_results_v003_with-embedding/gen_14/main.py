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
    Generates a well-typed STLC term optimized for variable usage and redex density.
    """
    
    # Counter for unique variable names to maximize unique subterms
    var_counter = 0

    def gen_type(size_limit: int) -> Ty:
        # Slightly higher probability for function types to increase complexity
        if size_limit <= 1 or rng.random() < 0.2:
            return rng.choice([("Bool",), ("Int",), ("String",)])
        split = rng.randint(1, max(1, size_limit - 1))
        return ("Fun", gen_type(split), gen_type(size_limit - split - 1))

    def gen_term(target_ty: Ty, ctx: List[Tuple[str, Ty]], budget: int) -> Tm:
        nonlocal var_counter
        
        valid_vars = [name for name, t in ctx if t == target_ty]

        # 1. Variable-Hungry Base Case: Force variable usage at leaves
        if budget <= 1:
            if valid_vars and rng.random() < 0.9:
                # Weighted selection: favor recently added variables
                weights = [(i + 1)**2 for i in range(len(valid_vars))]
                return ("Var", rng.choices(valid_vars, weights=weights, k=1)[0])
            
            # Fallbacks for base types
            if target_ty == ("Bool",): return ("Bool", rng.choice([True, False]))
            if target_ty == ("Int",): return ("Int", rng.randint(-500, 500))
            if target_ty == ("String",): return ("String", rng.choice(["s1", "s2", "s3"]))
            
            # Recursive fallback for function types (must return a Lam)
            if target_ty[0] == "Fun":
                var_counter += 1
                v = f"v{var_counter}"
                return ("Lam", v, target_ty[1], gen_term(target_ty[2], ctx + [(v, target_ty[1])], 0))
            return ("Int", 0)

        # 2. Weighted Constructor Selection
        choices, weights = [], []
        
        if target_ty[0] == "Fun":
            choices.append("lam"); weights.append(25)
        
        if valid_vars:
            choices.append("var"); weights.append(45) # High weight to boost used_vars
            
        if budget > 2:
            choices.append("app"); weights.append(55) # Highest weight for size/redexes
            
        if target_ty[0] != "Fun" or not choices:
            choices.append("lit"); weights.append(5)

        mode = rng.choices(choices, weights=weights)[0]

        if mode == "lam":
            var_counter += 1
            v_name = f"x{var_counter}"
            return ("Lam", v_name, target_ty[1], gen_term(target_ty[2], ctx + [(v_name, target_ty[1])], budget - 1))

        elif mode == "var":
            v_weights = [(i + 1)**2 for i in range(len(valid_vars))]
            return ("Var", rng.choices(valid_vars, weights=v_weights, k=1)[0])

        elif mode == "app":
            # 3. Context-Aware Argument Selection (70% chance)
            # Picking a type already in ctx makes it likely the arg branch can use a Var
            if ctx and rng.random() < 0.7:
                arg_ty = rng.choice(ctx)[1]
            else:
                arg_ty = gen_type(rng.randint(1, 3))

            # 4. Scaled Redex Injection
            # Probability increases with budget to ensure large terms have many redexes
            redex_prob = 0.35 + (budget / 150.0)
            split = rng.randint(1, budget - 1)
            
            if rng.random() < redex_prob and budget > 5:
                var_counter += 1
                v_name = f"r{var_counter}"
                # Construct (Lam v. body) arg
                f_tm = ("Lam", v_name, arg_ty, gen_term(target_ty, ctx + [(v_name, arg_ty)], split))
                a_tm = gen_term(arg_ty, ctx, budget - split - 1)
                return ("App", f_tm, a_tm)
            else:
                # Standard application
                return ("App", 
                        gen_term(("Fun", arg_ty, target_ty), ctx, split), 
                        gen_term(arg_ty, ctx, budget - split - 1))

        else: # lit
            if target_ty == ("Bool",): return ("Bool", rng.choice([True, False]))
            if target_ty == ("Int",): return ("Int", rng.randint(-1000, 1000))
            return ("String", f"val_{rng.randint(0, 9999)}")

    # Final generation with target limits
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