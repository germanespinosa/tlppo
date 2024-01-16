import tlppo
import typing
import cellworld


class CellworldObservation(tlppo.Observation):
    def __init__(self,
                 prey: cellworld.Location,
                 predator: typing. Union[cellworld.Location, None]):
        self.prey: typing.Tuple[float, ...] = (prey.x, prey.y)
        self.predator: typing.Union[typing.Tuple[float, ...], None] = None
        if predator:
            self.predator = (predator.x, predator.y)

