class DimensionedScalar:
    def __init__(
        self,
        values: list[str],
    ) -> None:
        self.values = values
        self.mass = values[0]
        self.length = values[1]
        self.time = values[2]
        self.temperature = values[3]
        self.quantity = values[4]
        self.current = values[5]
        self.luminous_intensity = values[6]

    def __str__(self) -> str:
        return "[" + " ".join(str(i) for i in self.values) + "]"

    def __repr__(self) -> str:
        return self.__str__()
