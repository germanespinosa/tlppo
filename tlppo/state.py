import typing
import math

class State(object):

    dimension_count: int = 2
    scale: typing.Tuple[float, ...] = (1.0, 1.0)
    origin: typing.Tuple[float, ...] = (0, 0)

    def __init__(self,
                 values: typing.Tuple[float, ...]):
        if len(values) != self.dimension_count:
            raise ValueError("state size does not match: found {}, expected {}".format(len(values), self.dimension_count))
        self.values: typing.Tuple[float, ...] = values
        self.magnitude: float = self.distance(other=self.origin)
        self.direction: typing.Tuple[float, ...] = self.atan(other=self.origin)

    def distance(self,
                 other: typing.Tuple[float, ...]) -> float:
        return sum((p1 - p2) ** 2 for p1, p2 in zip(self.values, other)) ** 0.5

    def atan(self,
             other: typing.Tuple[float, ...]) -> typing.Tuple[float, ...]:
        thetas: typing.List[float] = []
        for i in range(1, self.dimension_count):
            thetas.append(math.atan2(other[i] - self.values[i], other[i-1] - self.values[i-1]))
        return tuple(t for t in thetas)

    @classmethod
    def set_dimensions(cls,
                       dimension_count: int = 0,
                       scale: typing.Tuple[float, ...] = None):
        if dimension_count == 0 and scale is None:
            raise ValueError("either dimension_count or scale must be specified")
        if dimension_count == 0:
            dimension_count = len(scale)
        if scale is None:
            scale = [1.0 for i in range(dimension_count)]
        cls.dimensions = dimension_count
        cls.scale = scale
        cls.origin = tuple(0.0 for i in range(dimension_count))


class StateList(typing.List[State]):
    def find_closest(self,
                     state: State) -> State:
        if not self:
            raise ValueError("No states found")
        min_distance = float('inf')
        closest = None
        for s in self:
            distance = s.distance(other=state.values)
            if distance < min_distance:
                closest = s
        return closest

