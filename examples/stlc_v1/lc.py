from abc import abstractmethod
from dataclasses import dataclass
import inspect
import random
from typing import (
    Any,
    Callable,
    Dict,
    Generator,
    List,
    Literal,
    Set,
    Tuple,
)
from copy import deepcopy
import numpy as np
import tqdm


# ==============================================================================


class BugException(Exception):
    pass


class GrammarException(Exception):
    msgs: List[str]

    def __init__(self, *msgs: str):
        super().__init__()
        self.msgs = list(msgs)

    def __str__(self):
        return "\n".join(self.msgs)


class TypingException(Exception):
    msgs: List[str]

    def __init__(self, *msgs: str):
        super().__init__()
        self.msgs = list(msgs)

    def __str__(self):
        return "\n".join(self.msgs)


# ==============================================================================


class NameFormArg:
    name: str

    def __init__(self, name: str) -> None:
        self.name = name
        pass

    def __str__(self) -> str:
        return self.name


class LiteralFormArg:
    variants: List[str]

    def __init__(self, variants: List[str]) -> None:
        self.variants = variants

    def __str__(self) -> str:
        return ", ".join(self.variants)


class TypeFormArg:
    ty: type

    def __init__(self, ty: type) -> None:
        self.ty = ty

    def __str__(self) -> str:
        return self.ty.__name__


class Form:
    @abstractmethod
    def check(self, a: Any) -> Generator[Exception, Any, None]:
        pass


class MultiForm(Form):
    label: str
    variants: List[NameFormArg]

    def __init__(self, label, variants: List[NameFormArg]):
        self.label = label
        self.variants = variants

    def check(self, a: Any) -> Generator[Exception, Any, None]:

        # We have to do this here rather than in constructor since not all the
        # form are added to the dict yet.
        forms = list(map(getSingleForm, self.variants))

        if not isinstance(a, tuple):
            yield GrammarException(
                f"The construct {a} must be a tuple where the first component is the constructor and the rest of the components are the construct's arguments."
            )
            return None
        else:
            pass
        for form in forms:
            if form.constructor == a[0]:
                yield from form.check(a)
                return None
            else:
                pass
        yield GrammarException(
            f"The construct {a} is expected to be of the form '{self.label}', but it's constructor, '{a[0]}', is not a valid constructor for the form '{self.label}'. The valid constructors are: {", ".join([ f"'{form.constructor}'" for form in forms ])}."
        )


@dataclass
class SingleForm(Form):
    constructor: str
    params: List[TypeFormArg | LiteralFormArg | NameFormArg]

    def check(self, a: Any) -> Generator[Exception, Any, None]:
        if not isinstance(a, tuple):
            yield GrammarException(
                f"The value {a} could not be checked because it's not even a tuple."
            )
            return None

        if not a[0] == self.constructor:
            yield GrammarException(
                f"The value {a} must have constructor {self.constructor} in order to be checked by this Form."
            )
            return None

        template = f"({ ", ".join([f"'{self.constructor}'"] + [str(param) for param in self.params])})"
        correctUsage = f"To be constructed correctly, the '{self.constructor}' form must be constructed as a tuple in this format: {template}"

        if not len(a[1:]) == len(self.params):
            yield GrammarException(
                f"The construct {a} is not well-formed since the '{self.constructor}' form must have exactly {len(self.params)} arguments, but the construct has {len(a)} arguments. {correctUsage}"
            )
            return None
        else:
            pass

        for i, (arg, param) in enumerate(zip(a[1:], self.params)):
            if isinstance(param, TypeFormArg):
                if not isinstance(arg, param.ty):
                    yield GrammarException(
                        f"The construct {a} is not well-formed since the '{self.constructor}' form's argument {i} must be a '{param}', whereas {arg} was used. {correctUsage}"
                    )
                else:
                    pass

            elif isinstance(param, LiteralFormArg):
                if not isinstance(arg, str):
                    yield GrammarException(
                        f"The construct {a} is not well-formed since the '{self.constructor}' form's argument {i} must a str from the options {param.variants}, whereas the non-str {arg} was used. {correctUsage}"
                    )
                else:
                    pass

                if not arg in param.variants:
                    yield GrammarException(
                        f"The construct {a} is not well-formed since the '{self.constructor}' form's argument {i} must one of the options {", ".join([ f"'{param}'" for param in param.variants ])}, whereas {arg} was used. {correctUsage}"
                    )
                else:
                    pass

            elif isinstance(param, NameFormArg):
                form = allForms[param.name]
                yield from form.check(arg)
            else:
                raise Exception(f"Invalid form param: {param}")


def getSingleForm(v: NameFormArg) -> SingleForm:
    form = allForms[v.name]
    assert isinstance(form, SingleForm)
    return form


TyForm = MultiForm(
    label="Ty",
    variants=[
        NameFormArg("BoolTy"),
        NameFormArg("IntTy"),
        NameFormArg("StringTy"),
        NameFormArg("FunTy"),
    ],
)

TmForm = MultiForm(
    label="Tm",
    variants=[
        NameFormArg("BoolTm"),
        NameFormArg("IntTm"),
        NameFormArg("StringTm"),
        NameFormArg("VarTm"),
        NameFormArg("LamTm"),
        NameFormArg("AppTm"),
    ],
)

allForms: Dict[str, Form] = {
    #
    # types
    #
    "Ty": TyForm,
    "BoolTy": SingleForm(constructor="Bool", params=[]),
    "IntTy": SingleForm(constructor="Int", params=[]),
    "StringTy": SingleForm(constructor="String", params=[]),
    "FunTy": SingleForm(
        constructor="Fun",
        params=[NameFormArg("Ty"), NameFormArg("Ty")],
    ),
    #
    # terms
    #
    "Tm": TmForm,
    "BoolTm": SingleForm(constructor="Bool", params=[TypeFormArg(bool)]),
    "IntTm": SingleForm(constructor="Int", params=[TypeFormArg(int)]),
    "StringTm": SingleForm(constructor="String", params=[TypeFormArg(str)]),
    "VarTm": SingleForm(
        constructor="Var",
        params=[TypeFormArg(str)],
    ),
    "LamTm": SingleForm(
        constructor="Lam",
        params=[TypeFormArg(str), NameFormArg("Ty"), NameFormArg("Tm")],
    ),
    "AppTm": SingleForm(
        constructor="App",
        params=[NameFormArg("Tm"), NameFormArg("Tm")],
    ),
}

# ==============================================================================


type Ty = BoolTy | IntTy | StringTy | FunTy
type BoolTy = Tuple[Literal["Bool"]]
type IntTy = Tuple[Literal["Int"]]
type StringTy = Tuple[Literal["String"]]
type FunTy = Tuple[Literal["Fun"], Ty, Ty]

BoolTy_ = ("Bool",)
IntTy_ = ("Int",)
StringTy_ = ("String",)


# ==============================================================================


type Tm = LitTm | VarTm | LamTm | AppTm
type LitTm = (
    Tuple[Literal["Bool"], bool]
    | Tuple[Literal["Int"], int]
    | Tuple[Literal["String"], str]
)
type VarTm = Tuple[Literal["Var"], str]
type LamTm = Tuple[Literal["Lam"], str, Ty, Tm]
type AppTm = Tuple[Literal["App"], Tm, Tm]


# ==============================================================================


type Ctx = List[Tuple[str, Ty]]


# ==============================================================================


def lookup(ctx: Ctx, x: str) -> Generator[Exception, Any, Ty | None]:
    for c in ctx:
        if c[0] == x:
            return c[1]
        else:
            pass

    yield TypingException(f"The variable '{x}' is out of scope in context '{ctx}'.")


def extend(x: str, ty: Ty, ctx: Ctx) -> Ctx:
    ctx = deepcopy(ctx)
    ctx.append((x, ty))
    return ctx


# ==============================================================================


def validateTy(ty: Ty) -> Generator[Exception, Any, None]:
    yield from TyForm.check(ty)


def validateTm(a: Tm) -> Generator[Exception, Any, None]:
    yield from TmForm.check(a)


# ==============================================================================


def inferType(ctx: Ctx, tm: Tm) -> Generator[Exception, Any, Ty | None]:
    if tm[0] == "Bool":
        return ("Bool",)
    elif tm[0] == "Int":
        return ("Int",)
    elif tm[0] == "String":
        return ("String",)
    elif tm[0] == "Var":
        _, x = tm
        yield from lookup(ctx, x)
    elif tm[0] == "Lam":
        _, x, alpha, b = tm
        beta = yield from inferType(extend(x, alpha, ctx), b)
        if beta is None:
            return None
        else:
            pass

        return ("Fun", alpha, beta)
    elif tm[0] == "App":
        _, f, a = tm
        phi = yield from inferType(ctx, f)
        if phi is None:
            return None
        else:
            pass

        if phi[0] == "Fun":
            _, alpha, beta = phi
            yield from checkType_aux(ctx, alpha, a)
        else:
            yield TypingException(
                f"The term {f} was applied to the argument {a}, so it is expected to have a function type, but it actually has type {phi}"
            )
            return None
    else:
        raise BugException(f"Unhandled term constructor '{tm[0]}' in term: {tm}")


def eqTy(ty1: Ty, ty2: Ty) -> bool:

    if len(ty1) == 0:
        raise BugException(f"Not well-formed type: {ty1}")

    if len(ty2) == 0:
        raise BugException(f"Not well-formed type: {ty0}")

    for x1, x2 in zip(ty1, ty2):
        if isinstance(x1, str) and isinstance(x2, str):
            if x1 != x2:
                return False
        elif isinstance(x1, tuple) and isinstance(x2, tuple):
            if not eqTy(x1, x2):
                return False
        else:
            raise BugException(f"Not well-formed type (one of them): {x1}, {x2}")

    return True


def checkType_aux(ctx: Ctx, ty_expected: Ty, tm: Tm) -> Generator[Exception, Any, None]:

    if tm[0] == "Bool":
        if not eqTy(ty_expected, BoolTy_):
            yield TypingException(
                f"The term {tm} is expected to have type {ty_expected}, but it actually has type {BoolTy_}"
            )
        else:
            pass

    elif tm[0] == "Int":
        if not eqTy(ty_expected, IntTy_):
            yield TypingException(
                f"The term {tm} is expected to have type {ty_expected}, but it actually has type {IntTy_}"
            )
        else:
            pass

    elif tm[0] == "String":
        if not eqTy(ty_expected, StringTy_):
            yield TypingException(
                f"The term {tm} is expected to have type {ty_expected}, but it actually has type {StringTy_}"
            )

    elif tm[0] == "Var":
        _, x = tm
        ty_actual = yield from lookup(ctx, x)
        if ty_actual is None:
            return None
        elif not eqTy(ty_actual, ty_expected):
            yield TypingException(
                f"The variable '{x}' is expected to have type {ty_expected} but it actually has type {ty_actual}."
            )
        else:
            pass

    elif tm[0] == "Lam":
        _, x, alpha_actual, b = tm
        if ty_expected[0] == "Fun":
            _, alpha_expected, beta = ty_expected
            if not eqTy(alpha_actual, alpha_expected):
                yield TypingException(
                    f"The term {tm} is a function that is expected to have domain {alpha_expected}, but it actually has domain {alpha_actual}."
                )
            else:
                pass

            alpha = alpha_actual
            ctx = extend(x, alpha, ctx)
            yield from checkType_aux(ctx, beta, b)
        else:
            yield TypingException(
                f"The term {tm} is expected to have the non-function type {ty_expected}, but it is a lambda and so actually has a function type."
            )

    elif tm[0] == "App":
        _, f, a = tm
        phi = yield from inferType(ctx, f)
        if phi is None:
            return None
        elif phi[0] == "Fun":
            _, alpha, beta = phi
            yield from checkType_aux(ctx, alpha, a)
        else:
            yield TypingException(
                f"The term {f} was applied to the argument {a}, so it is expected to have a function type, but it actually has type {phi}"
            )
            return None

    else:
        raise BugException(f"Unhandled term constructor '{tm[0]}' in term: {tm}")


def checkType(ty: Ty, tm: Tm) -> Generator[Exception, Any, None]:
    yield from checkType_aux([], ty, tm)


# ==============================================================================


def check_aux(ty: Any, tm: Any) -> Generator[Exception, Any, None]:
    validateTy_exns = list(validateTy(ty))
    validateTm_exns = list(validateTm(tm))
    validate_exns = validateTy_exns + validateTm_exns
    if len(validate_exns) != 0:
        for e in validate_exns:
            yield e
    else:
        yield from checkType(ty, tm)


def check(ty: Any, tm: Any) -> List[Exception]:
    return list(check_aux(ty, tm))


# ------------------------------------------------------------------------------


def size_of_tuple(t: Tuple) -> int:
    n = 1
    for x in t:
        if isinstance(x, tuple):
            n = max(n, 1 + size_of_tuple(x))
    return n


# ------------------------------------------------------------------------------

type RunOutput = Tuple[List[GoodResult], List[BadResult], List[ErrorResult]]


@dataclass
class GoodResult:
    ty: Ty
    tm: Tm

    def ty_size(self) -> int:
        return size_of_tuple(self.ty)

    def tm_size(self) -> int:
        return size_of_tuple(self.tm)

    def used_vars_proportion(self) -> float:
        var_idx = 0

        def next_var_idx():
            nonlocal var_idx
            x = var_idx
            var_idx += 1
            return x

        all_vars: Set[Tuple[str, int]] = set()
        used_vars: Set[Tuple[str, int]] = set()

        def lookup(ctx: List[Tuple[str, int]], x: str) -> Tuple[str, int]:
            for c in ctx:
                if c[0] == x:
                    return c
                else:
                    pass

            raise Exception(
                f"Impossible, out-of-scope variable '{x}' in a well-formed term in context {ctx}"
            )

        def go(tm: Tm, ctx: List[Tuple[str, int]]):
            ctx = ctx[:]  # shallow copy

            if tm[0] == "Lam":
                _, x, alpha, b = tm
                v = (x, next_var_idx())

                all_vars.add(v)

                ctx.append(v)
                go(b, ctx)

            elif tm[0] == "Var":
                _, x = tm
                v = lookup(ctx, x)
                used_vars.add(v)

            elif tm[0] == "App":
                _, f, a = tm
                go(f, ctx)
                go(a, ctx)

            elif tm[0] == "Bool" or tm[0] == "Int" or tm[0] == "String":
                pass

            else:
                raise Exception(
                    f"Impossible, unrecognized term label '{tm[0]}' in a well-formed term "
                )

        go(tm=self.tm, ctx=[])

        return len(used_vars) / (len(all_vars) + 1)

    def applied_lambdas_proportion(self) -> float:
        lambdas_count = 0
        applied_lambdas_count = 0

        def go(tm: Tm):
            nonlocal lambdas_count
            nonlocal applied_lambdas_count

            if tm[0] == "Lam":
                _, x, alpha, b = tm

                lambdas_count += 1

                go(b)

            elif tm[0] == "App":
                _, f, a = tm

                if f[0] == "Lam":
                    applied_lambdas_count += 1

                go(f)
                go(a)

            elif (
                tm[0] == "Bool" or tm[0] == "Int" or tm[0] == "String" or tm[0] == "Var"
            ):
                pass

            else:
                raise Exception(
                    f"Impossible, unrecognized term label '{tm[0]}' in a well-formed term "
                )

        go(self.tm)

        return applied_lambdas_count / (lambdas_count + 1)

    def unique_subterms_proportion(self) -> float:
        unique_subterms: Set[Tm] = set()
        subterms_count = 0

        def go(tm: Tm):
            nonlocal subterms_count

            if tm[0] == "Lam":
                _, x, alpha, b = tm

                subterms_count += 1
                unique_subterms.add(tm)

                go(b)

            elif tm[0] == "App":
                _, f, a = tm

                subterms_count += 1
                unique_subterms.add(tm)

                go(f)
                go(a)

            elif (
                tm[0] == "Bool" or tm[0] == "Int" or tm[0] == "String" or tm[0] == "Var"
            ):
                pass

            else:
                raise Exception(
                    f"Impossible, unrecognized term label '{tm[0]}' in a well-formed term "
                )

        go(self.tm)

        return len(unique_subterms) / (subterms_count + 1)


@dataclass
class BadResult:
    result: Tuple[Ty, Tm] | None
    exns: List[Exception]

    def show_verbosely(self) -> str:
        if self.result is None:
            return f"""
Encountered exceptions when generating a type and term:

{"\n".join([ f"- {exn}" for exn in self.exns ])}
""".strip()

        else:
            ty, tm = self.result
            return f"""
Successfully generated type {ty} and term {tm}. However, these exceptions were yielded from grammar and typing checks:

{"\n".join([ f"- {exn}" for exn in self.exns ])}
""".strip()


@dataclass
class ErrorResult:
    exn: Exception

    def show_verbosely(self) -> str:
        return "TODO"


def run(
    size: int,
    rng: random.Random,
    generate_sample: Callable[[random.Random], Tuple[Ty, Tm]],
) -> RunOutput:
    goods: List[GoodResult] = []
    bads: List[BadResult] = []
    errors: List[ErrorResult] = []

    for _ in tqdm.tqdm(
        iterable=range(size),
        desc="Generating and checking samples",
    ):
        try:
            ty, tm = generate_sample(rng)
            exns = check(ty, tm)

            if len(exns) == 0:
                goods.append(GoodResult(ty, tm))
            else:
                bads.append(BadResult((ty, tm), exns))
        except BugException as exn:
            raise exn
        except Exception as exn:
            errors.append(ErrorResult(exn))

    return goods, bads, errors
