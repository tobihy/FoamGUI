from typing import Union

from model.core.values import Scalar, Tensor


class Element:
    def __init__(self, name: str) -> None:
        self.name = name

    def __str__(self) -> str:
        return self.name


class FieldElement(Element):
    def __init__(self, name: str, value: Union[str, Scalar, Tensor]) -> None:
        super().__init__(name)
        self.value = value

    def __str__(self) -> str:
        return self.name + " " + str(self.value)
