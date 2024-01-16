import random
import typing
from .state import State
from .observation import Observation


class Particle(object):
    def evolve(self,
               state: State,
               next_state: State) -> "Particle":
        raise NotImplementedError()


class ParticleFilter(object):

    def __init__(self):
        self.history: typing.List[Observation] = list()

    def update_history(self, observation: Observation) -> None:
        self.history.append(observation)

    def is_valid(self, particle: Particle) -> bool:
        raise NotImplementedError()

    def new_particle(self) -> Particle:
        raise NotImplementedError()


class BeliefState(object):

    def __init__(self,
                 size: int,
                 particle_filter: ParticleFilter):
        self.size: int = size
        self.particles: typing.List[Particle] = list()
        self.particle_filter: ParticleFilter = particle_filter

    def filter(self,
               observation: Observation):
        filtered: typing.List[Particle] = list()
        self.particle_filter.update_history(observation=observation)
        for particle in self.particles:
            if not self.particle_filter.is_valid(particle=particle):
                filtered.append(particle)
        self.particles = filtered
        return len(self.particles)

    def complete(self,
                 attempts: int = 100) -> int:
        for attempt in range(attempts):
            if len(self.particles) >= self.size:
                break
            candidate = self.particle_filter.new_particle()
            if self.particle_filter.is_valid(candidate):
                self.particles.append(candidate)
        return len(self.particles)

    def get_particle(self) -> Particle:
        return random.choice(self.particles)

