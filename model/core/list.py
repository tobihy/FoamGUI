class List(list):
    def __init__(self, elements: list[str]) -> None:
        super().__init__(elements)

    def __str__(self) -> str:
        return "(" + " ".join(str(el) for el in self) + ")"

    def __repr__(self) -> str:
        return self.__str__()
