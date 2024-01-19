import random
import typing
from .state import State
from .observation import Observation


class Particle(object):
    def evolve(self,
               state: State,
               next_state: State) -> "Particle":
        raise NotImplementedError()


class BeliefState(object):

    def __init__(self):
        self.particles: typing.List[Particle] = list()
        self.history: typing.List[Observation] = list()

    def update_history(self, observation: Observation) -> None:
        self.history.append(observation)

    def get_particle(self) -> Particle:
        return random.choice(self.particles)

