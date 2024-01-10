import typing
from .state import State
import random


class StatePathFinder:
    def get_path(self,
                 src: typing.Union[State, typing.Tuple[float, ...]],
                 dst: typing.Union[State, typing.Tuple[float, ...]]) -> typing.List[typing.Tuple[float, ...]]:
        raise NotImplementedError()


class Particle(object):
    def __init__(self, state: State):
        self._state: State = state
        self._destination: State = State(values=state.values)
        self._direction: typing.Tuple[float, ...] = tuple()
        self.path: typing.List[typing.Tuple[float, ...]] = list()

    @property
    def destination(self) -> State:
        return self._destination

    @destination.setter
    def destination(self, state: State):
        self._destination = state
        self._direction = self._state.direction(other=self._destination.values)

    @property
    def state(self) -> State:
        return self._state

    @state.setter
    def state(self, state: State):
        self._state = state

    @property
    def direction(self):
        return self._direction

    def distance(self):
        return self.state.distance(other=self.destination.values)

    def evolve(self,
               delta_d: float) -> "Particle":
        distance = self.distance()
        while distance < delta_d:
            self.state = self.destination
            delta_d -= distance
            if self.path:
                destination = State(values=self.path[0])
                self.destination = destination
                self.path = self.path[1:]
            else:
                return self
            distance = self.distance()
        self.state = self.state.move(self.direction, delta_d)
        return self


class LineOfSight(object):
    def is_visible(self,
                   src: typing.Union[State, typing.Tuple[float, ...]],
                   dst: typing.Union[State, typing.Tuple[float, ...]]) -> bool:
        raise NotImplementedError()


class PredatorModel(object):

    def __init__(self,
                 speed_ratio: float,
                 destinations: typing.List[typing.Tuple[float, ...]],
                 path_finder: StatePathFinder,
                 line_of_sight: LineOfSight):
        self.speed_ratio: float = speed_ratio
        self.destinations: typing.List[typing.Tuple[float, ...]] = destinations
        self.path_finder: StatePathFinder = path_finder
        self.line_of_sight: LineOfSight = line_of_sight

    def exploration_destination(self,
                                observer: typing.Tuple[float, ...]) -> typing.Union[typing.Tuple[float, ...], None]:
        hidden_destinations = [destination for destination in self.destinations
                               if not self.line_of_sight.is_visible(observer, destination)]
        if hidden_destinations:
            return random.choice(hidden_destinations)

        return None

    def predict(self,
                predator_state: Particle,
                prey_state: State,
                prey_next_state: State) -> Particle:
        if self.line_of_sight.is_visible(prey_state,
                                         prey_next_state):
            predator_state.destination.values = prey_next_state.values
        else:
            if predator_state.distance() == 0:
                destination = self.exploration_destination(predator_state.state.values)
                predator_state.destination.path = self.path_finder.get_path(predator_state.state, destination)

        delta_d = prey_next_state.distance(prey_state.values) * self.speed_ratio
        return predator_state.evolve(delta_d=delta_d)


class ParticleSource(object):
    def get_particle(self) -> Particle:
        raise NotImplementedError()


class ParticleFilter(object):

    def __init__(self,
                 size: int,
                 particles_source: ParticleSource,
                 predator_model: PredatorModel,
                 line_of_sight: LineOfSight):
        self.size: int = size
        self.particles: typing.List[Particle] = list()
        self.particles_source: ParticleSource = particles_source
        self.predator_model: PredatorModel = predator_model
        self.line_of_sight: LineOfSight = line_of_sight

    def filter(self,
               observer: typing.Tuple[float, ...]):
        filtered: typing.List[Particle] = list()
        for particle in self.particles:
            if not self.line_of_sight.is_visible(src=observer,
                                                 dst=particle.state.values):
                filtered.append(particle)
        self.particles = filtered

    def complete(self,
                 observer: typing.Tuple[float, ...],
                 attempts: int = 100):
        for attempt in range(attempts):
            if len(self.particles) >= self.size:
                break
            candidate = self.particles_source.get_particle()
            if self.line_of_sight.is_visible(observer, candidate.state):
                self.particles.append(candidate)
        return len(self.particles)
