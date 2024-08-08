from typing import Union

from util.constants import NEWLINE, NONUNIFORM, SPACER, UNIFORM


class Scalar:
    def __init__(self, value: str) -> None:
        self.value = value

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        return self.__str__()


class Tensor:
    def __init__(self, components: list) -> None:
        self.components = components

    def __str__(self) -> str:
        return "(" + " ".join(str(v) for v in self.components) + ")"

    def __repr__(self) -> str:
        return self.__str__()


class List:
    def __init__(self, lst: list, len=None, el=None) -> None:
        self.lst = lst
        self.len = len
        self.el = el

    def __str__(self) -> str:
        base = "(" + " ".join(map(str, self.lst)) + ")"
        if self.len:
            base = str(self.len) + NEWLINE + base
        if self.el:
            base = str(self.el) + NEWLINE + base
        return base


class Value:
    def __init__(self, uniform: bool, value: Union[Scalar, Tensor, List]) -> None:
        self.uniform = uniform
        self.value = value

    def __str__(self) -> str:
        return (UNIFORM if self.uniform else NONUNIFORM) + SPACER + str(self.value)

    def __repr__(self) -> str:
        return self.__str__()
