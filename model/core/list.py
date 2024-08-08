from typing import List


class List(List):
    def __init__(self, elements: List[str]) -> None:
        super().__init__(elements)

    def __str__(self) -> str:
        return "(" + " ".join(str(el) for el in self) + ")"

    def __repr__(self) -> str:
        return self.__str__()
