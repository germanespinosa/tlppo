import typing

from .state import State
from .particle import Particle


class EvaluationFunction(object):
    def evaluate(self, state: State, particle: Particle) -> typing.Tuple[float, bool]:
        raise NotImplementedError()
