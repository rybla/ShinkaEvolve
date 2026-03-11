from abc import abstractmethod
from dataclasses import dataclass
from typing import (
    Any,
    Dict,
    Generator,
    List,
    Literal,
    Tuple,
)
from copy import deepcopy


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
        # We have to do this here rather than in constructor since not all the
        # form are added to the dict yet.
        forms = list(map(getSingleForm, self.variants))

        if not isinstance(a, tuple):
            yield CheckingException(
                f"The construct {a} must be a tuple where the first component is the constructor and the rest of the components are the construct's arguments."
            )
            return

        for form in forms:
            if form.constructor == a[0]:
                yield from form.check(a)
                return

        yield CheckingException(
            f"The construct {a} is expected to be of the form '{self.label}', but it's constructor, '{a[0]}', is not a valid constructor for the form '{self.label}'. The valid constructors are: {", ".join([ f"'{form.constructor}'" for form in forms ])}."
        )


@dataclass
class SingleForm(Form):
    constructor: str
    params: List[TypeFormArg | LiteralFormArg | NameFormArg]

    def check(self, a: Any) -> Generator[CheckingException, Any, None]:
        assert isinstance(a, tuple)
        assert a[0] == self.constructor

        template = f"({ ", ".join([f"'{self.constructor}'"] + [str(param) for param in self.params])})"
        correctUsage = f"To be constructed correctly, the '{self.constructor}' form must be constructed as a tuple in this format: {template}"

        if not len(a[1:]) == len(self.params):
            yield CheckingException(
                f"The construct {a} is not well-formed since the '{self.constructor}' form must have exactly {len(self.params)} arguments, but the construct has {len(a)} arguments. {correctUsage}"
            )
            return

        for i, (arg, param) in enumerate(zip(a[1:], self.params)):
            if isinstance(param, TypeFormArg):
                if not isinstance(arg, param.ty):
                    yield CheckingException(
                        f"The construct {a} is not well-formed since the '{self.constructor}' form's {i}th argument must be a '{param}', whereas {arg} was used. {correctUsage}"
                    )
            elif isinstance(param, LiteralFormArg):
                if not isinstance(arg, str):
                    yield CheckingException(
                        f"The construct {a} is not well-formed since the '{self.constructor}' form's {i}th argument must a str from the options {param.variants}, whereas the non-str {arg} was used. {correctUsage}"
                    )
                if not arg in param.variants:
                    yield CheckingException(
                        f"The construct {a} is not well-formed since the '{self.constructor}' form's {i}th argument must one of the options {", ".join([ f"'{param}'" for param in param.variants ])}, whereas {arg} was used. {correctUsage}"
                    )
            elif isinstance(param, NameFormArg):
                form = allForms[param.name]
                yield from form.check(arg)
            else:
                raise Exception(f"Invalid form param: {param}")


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

    @classmethod
    def union(cls, errs: List[CheckingException]) -> CheckingException:
        msgs: List[str] = []
        for err in errs:
            for msg in err.msgs:
                msgs.append(msg)
        return CheckingException(*msgs)

    def __str__(self):
        return "\n".join(self.msgs)


# ==============================================================================


def lookup(ctx: Ctx, x: str) -> Generator[CheckingException, Any, Ty | None]:
    for c in ctx:
        if c[0] == x:
            return c[1]
    yield CheckingException(f"The variable '{x}' is out of scope in context '{ctx}'.")


def extend(x: str, ty: Ty, ctx: Ctx) -> Ctx:
    ctx = deepcopy(ctx)
    ctx.append((x, ty))
    return ctx


# ==============================================================================


def validateTy(ty: Ty) -> Generator[CheckingException, Any, None]:
    yield from TyForm.check(ty)


def validateTm(a: Tm) -> Generator[CheckingException, Any, None]:
    yield from TmForm.check(a)


# ==============================================================================


def inferType(ctx: Ctx, tm: Tm) -> Generator[CheckingException, Any, Ty | None]:
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
        return ("Fun", alpha, beta)
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


def checkType_aux(
    ctx: Ctx, ty_expected: Ty, tm: Tm
) -> Generator[CheckingException, Any, None]:
    if tm[0] == "Bool":
        if not eqTy(ty_expected, BoolTy_):
            yield CheckingException(
                f"The term {tm} is expected to have type {ty_expected}, but it actually has type {BoolTy_}"
            )

    elif tm[0] == "Int":
        if not eqTy(ty_expected, IntTy_):
            yield CheckingException(
                f"The term {tm} is expected to have type {ty_expected}, but it actually has type {IntTy_}"
            )

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
    return list(check_aux(ty, tm))
