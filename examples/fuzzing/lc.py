from abc import abstractmethod
from dataclasses import dataclass
import inspect
from typing import (
    Any,
    Dict,
    Generator,
    List,
    Literal,
    Set,
    Tuple,
)
from copy import deepcopy
import numpy as np


# ==============================================================================


class CoverageManager:
    def __init__(self):
        self.trace: List[str] = []
        self.function_names: Set[str] = set()
        self.labels: Set[str] = set()

    def record(self, value: Any = None, weight=1):
        stack_trace = inspect.stack(0)
        frame_info = stack_trace[1]
        function_name = frame_info.function
        line_number = frame_info.lineno
        label = f"lc.py:{line_number} {function_name} {value}"

        self.trace.append(label)
        self.function_names.add(function_name)
        self.labels.add(label)

        del stack_trace

    def reset(self):
        self.trace = []
        self.function_names = set()
        self.labels = set()


coverageManager = CoverageManager()


def reset_coverageManager():
    coverageManager.reset()


class CoverageReport:

    def __init__(self):
        self.function_names_batches: List[Set[str]] = []
        self.labels_batches: List[Set[str]] = []

    def add(self, cm: CoverageManager):
        self.function_names_batches.append(cm.function_names)
        self.labels_batches.append(cm.labels)

    def average_number_of_function_names(self):
        return np.average(
            [len(function_names) for function_names in self.function_names_batches]
        )

    def average_number_of_labels(self):
        return np.average([len(labels) for labels in self.labels_batches])


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
    def check(self, a: Any) -> Generator[CheckingException, Any, None]:
        pass


def getSingleForm(v: NameFormArg) -> SingleForm:
    form = allForms[v.name]
    assert isinstance(form, SingleForm)
    return form


class MultiForm(Form):
    label: str
    variants: List[NameFormArg]

    def __init__(self, label, variants: List[NameFormArg]):
        self.label = label
        self.variants = variants

    def check(self, a: Any) -> Generator[CheckingException, Any, None]:
        coverageManager.record(value=self.label)

        # We have to do this here rather than in constructor since not all the
        # form are added to the dict yet.
        forms = list(map(getSingleForm, self.variants))

        if not isinstance(a, tuple):
            coverageManager.record(value=self.label)
            yield CheckingException(
                f"The construct {a} must be a tuple where the first component is the constructor and the rest of the components are the construct's arguments."
            )
            return None
        else:
            coverageManager.record(value=self.label)

        for form in forms:
            coverageManager.record(value=self.label)
            if form.constructor == a[0]:
                coverageManager.record(value=self.label)
                yield from form.check(a)
                return None
            else:
                coverageManager.record(value=self.label)

        yield CheckingException(
            f"The construct {a} is expected to be of the form '{self.label}', but it's constructor, '{a[0]}', is not a valid constructor for the form '{self.label}'. The valid constructors are: {", ".join([ f"'{form.constructor}'" for form in forms ])}."
        )


@dataclass
class SingleForm(Form):
    constructor: str
    params: List[TypeFormArg | LiteralFormArg | NameFormArg]

    def check(self, a: Any) -> Generator[CheckingException, Any, None]:
        if not isinstance(a, tuple):
            coverageManager.record(value=self.constructor)
            yield CheckingException(
                f"The value {a} could not be checked because it's not even a tuple."
            )
            return None

        if not a[0] == self.constructor:
            coverageManager.record(value=self.constructor)
            yield CheckingException(
                f"The value {a} must have constructor {self.constructor} in order to be checked by this Form."
            )
            return None

        coverageManager.record(value=self.constructor)

        template = f"({ ", ".join([f"'{self.constructor}'"] + [str(param) for param in self.params])})"
        correctUsage = f"To be constructed correctly, the '{self.constructor}' form must be constructed as a tuple in this format: {template}"

        if not len(a[1:]) == len(self.params):
            coverageManager.record(value=self.constructor)
            yield CheckingException(
                f"The construct {a} is not well-formed since the '{self.constructor}' form must have exactly {len(self.params)} arguments, but the construct has {len(a)} arguments. {correctUsage}"
            )
            return None
        else:
            coverageManager.record(value=self.constructor)

        for i, (arg, param) in enumerate(zip(a[1:], self.params)):
            coverageManager.record(value=(self.constructor, i))
            if isinstance(param, TypeFormArg):
                coverageManager.record(value=self.constructor)
                if not isinstance(arg, param.ty):
                    coverageManager.record(value=self.constructor)
                    yield CheckingException(
                        f"The construct {a} is not well-formed since the '{self.constructor}' form's {i}th argument must be a '{param}', whereas {arg} was used. {correctUsage}"
                    )
                else:
                    coverageManager.record(value=self.constructor)
            elif isinstance(param, LiteralFormArg):
                coverageManager.record(value=self.constructor)
                if not isinstance(arg, str):
                    coverageManager.record(value=self.constructor)
                    yield CheckingException(
                        f"The construct {a} is not well-formed since the '{self.constructor}' form's {i}th argument must a str from the options {param.variants}, whereas the non-str {arg} was used. {correctUsage}"
                    )
                else:
                    coverageManager.record(value=self.constructor)
                if not arg in param.variants:
                    coverageManager.record(value=self.constructor)
                    yield CheckingException(
                        f"The construct {a} is not well-formed since the '{self.constructor}' form's {i}th argument must one of the options {", ".join([ f"'{param}'" for param in param.variants ])}, whereas {arg} was used. {correctUsage}"
                    )
                else:
                    coverageManager.record(value=self.constructor)
            elif isinstance(param, NameFormArg):
                coverageManager.record(value=self.constructor)
                form = allForms[param.name]
                yield from form.check(arg)
            else:
                coverageManager.record(value=self.constructor)
                raise Exception(f"Invalid form param: {param}")

        coverageManager.record(value=self.constructor)


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


class BugException(Exception):
    pass


class CheckingException(Exception):
    msgs: List[str]

    def __init__(self, *msgs: str):
        super().__init__()
        self.msgs = list(msgs)

    def __str__(self):
        return "\n".join(self.msgs)


# ==============================================================================


def lookup(ctx: Ctx, x: str) -> Generator[CheckingException, Any, Ty | None]:
    for c in ctx:
        if c[0] == x:
            coverageManager.record()
            return c[1]
        else:
            coverageManager.record()
    coverageManager.record()
    yield CheckingException(f"The variable '{x}' is out of scope in context '{ctx}'.")


def extend(x: str, ty: Ty, ctx: Ctx) -> Ctx:
    coverageManager.record()
    ctx = deepcopy(ctx)
    ctx.append((x, ty))
    return ctx


# ==============================================================================


def validateTy(ty: Ty) -> Generator[CheckingException, Any, None]:
    coverageManager.record()
    yield from TyForm.check(ty)


def validateTm(a: Tm) -> Generator[CheckingException, Any, None]:
    coverageManager.record()
    yield from TmForm.check(a)


# ==============================================================================


def inferType(ctx: Ctx, tm: Tm) -> Generator[CheckingException, Any, Ty | None]:
    if tm[0] == "Bool":
        coverageManager.record()
        return ("Bool",)
    elif tm[0] == "Int":
        coverageManager.record()
        return ("Int",)
    elif tm[0] == "String":
        coverageManager.record()
        return ("String",)
    elif tm[0] == "Var":
        coverageManager.record()
        _, x = tm
        yield from lookup(ctx, x)
    elif tm[0] == "Lam":
        coverageManager.record()
        _, x, alpha, b = tm
        beta = yield from inferType(extend(x, alpha, ctx), b)
        if beta is None:
            coverageManager.record()
            return None
        else:
            coverageManager.record()
        return ("Fun", alpha, beta)
    elif tm[0] == "App":
        coverageManager.record()
        _, f, a = tm
        phi = yield from inferType(ctx, f)
        if phi is None:
            return None
        else:
            coverageManager.record()
        if phi[0] == "Fun":
            coverageManager.record()
            _, alpha, beta = phi
            yield from checkType_aux(ctx, alpha, a)
        else:
            coverageManager.record()
            yield CheckingException(
                f"The term {f} was applied to the argument {a}, so it is expected to have a function type, but it actually has type {phi}"
            )
            return None
    else:
        coverageManager.record()
        raise BugException(f"Unhandled term constructor '{tm[0]}' in term: {tm}")


def eqTy(ty1: Ty, ty2: Ty) -> bool:
    coverageManager.record()

    if len(ty1) == 0:
        coverageManager.record()
        raise BugException(f"Not well-formed type: {ty1}")

    if len(ty2) == 0:
        coverageManager.record()
        raise BugException(f"Not well-formed type: {ty0}")

    for x1, x2 in zip(ty1, ty2):
        if isinstance(x1, str) and isinstance(x2, str):
            coverageManager.record()
            if x1 != x2:
                coverageManager.record()
                return False
            coverageManager.record()
        elif isinstance(x1, tuple) and isinstance(x2, tuple):
            coverageManager.record()
            if not eqTy(x1, x2):
                coverageManager.record()
                return False
            coverageManager.record()
        else:
            coverageManager.record()
            raise BugException(f"Not well-formed type (one of them): {x1}, {x2}")

    coverageManager.record()
    return True


def checkType_aux(
    ctx: Ctx, ty_expected: Ty, tm: Tm
) -> Generator[CheckingException, Any, None]:
    coverageManager.record()

    if tm[0] == "Bool":
        coverageManager.record()
        if not eqTy(ty_expected, BoolTy_):
            coverageManager.record()
            yield CheckingException(
                f"The term {tm} is expected to have type {ty_expected}, but it actually has type {BoolTy_}"
            )
        else:
            coverageManager.record()

    elif tm[0] == "Int":
        coverageManager.record()
        if not eqTy(ty_expected, IntTy_):
            coverageManager.record()
            yield CheckingException(
                f"The term {tm} is expected to have type {ty_expected}, but it actually has type {IntTy_}"
            )
        else:
            coverageManager.record()

    elif tm[0] == "String":
        if not eqTy(ty_expected, StringTy_):
            yield CheckingException(
                f"The term {tm} is expected to have type {ty_expected}, but it actually has type {StringTy_}"
            )

    elif tm[0] == "Var":
        _, x = tm
        ty_actual = yield from lookup(ctx, x)
        if ty_actual is None:
            return None
        elif not eqTy(ty_actual, ty_expected):
            yield CheckingException(
                f"The variable '{x}' is expected to have type {ty_expected} but it actually has type {ty_actual}."
            )

    elif tm[0] == "Lam":
        _, x, alpha_actual, b = tm
        if ty_expected[0] == "Fun":
            _, alpha_expected, beta = ty_expected
            if not eqTy(alpha_actual, alpha_expected):
                yield CheckingException(
                    f"The term {tm} is a function that is expected to have domain {alpha_expected}, but it actually has domain {alpha_actual}."
                )
            alpha = alpha_actual
            ctx = extend(x, alpha, ctx)
            yield from checkType_aux(ctx, beta, b)
        else:
            yield CheckingException(
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
            yield CheckingException(
                f"The term {f} was applied to the argument {a}, so it is expected to have a function type, but it actually has type {phi}"
            )
            return None

    else:
        raise BugException(f"Unhandled term constructor '{tm[0]}' in term: {tm}")


def checkType(ty: Ty, tm: Tm) -> Generator[CheckingException, Any, None]:
    yield from checkType_aux([], ty, tm)


# ==============================================================================


def check_aux(ty: Any, tm: Any) -> Generator[CheckingException, Any, None]:
    validateTy_errs = list(validateTy(ty))
    validateTm_errs = list(validateTm(tm))
    validate_errs = validateTy_errs + validateTm_errs
    if len(validate_errs) != 0:
        for e in validate_errs:
            yield e
    else:
        yield from checkType(ty, tm)


def check(ty: Any, tm: Any) -> List[CheckingException]:
    coverageManager.reset()
    return list(check_aux(ty, tm))


def check_coverage(samples: List[Tuple[Ty, Tm]]):
    coverageReport = CoverageReport()

    for sample in samples:
        print()
        ty, tm = sample
        print(f"ty = {ty}")
        print(f"tm = {tm}")
        errs = check(ty, tm)
        for err in errs:
            print(f"  - {err}")

        coverageReport.add(coverageManager)
        coverageManager.reset()

    print(
        f"average_number_of_function_names = {coverageReport.average_number_of_function_names()}"
    )
    print(f"average_number_of_labels = {coverageReport.average_number_of_labels()}")

    return coverageReport
