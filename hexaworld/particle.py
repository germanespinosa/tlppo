import tlppo
import typing

from tlppo import Particle
from .observation import CellworldObservation
from .path_finder import PathFinder
from .line_of_sight import LineOfSight
import cellworld
import random


class CellworldParticle(tlppo.Particle):
    def __init__(self,
                 state: tlppo.State,
                 line_of_sight: LineOfSight,
                 path_finder: PathFinder,
                 path: typing.List[typing.Tuple[float, ...]] = None):
        self.state: tlppo.State = state
        self.line_of_sight: LineOfSight = line_of_sight
        self.destination: tlppo.State = tlppo.State(values=state.values)
        self.direction: typing.Tuple[float, ...] = tuple()
        self.path: typing.List[typing.Tuple[float, ...]]
        if path is not None:
            self.path = path
        else:
            self.path = []
        self.path_finder: PathFinder = path_finder

    def set_direction(self):
        if self.state.values != self.destination.values:
            self.direction = self.state.direction(other=self.destination.values)
        else:
            self.direction = tlppo.State.origin

    def distance(self):
        return self.state.distance(other=self.destination.values)

    def __copy__(self):
        new_particle = CellworldParticle(state=self.state,
                                         line_of_sight=self.line_of_sight,
                                         path_finder=self.path_finder)
        new_particle.destination = self.destination
        new_particle.path = [step for step in self.path]
        return new_particle

    def evolve(self,
               state: tlppo.State,
               next_state: tlppo.State) -> "Particle":

        evolved = CellworldParticle(state=self.state,
                                    line_of_sight=self.line_of_sight,
                                    path_finder=self.path_finder,
                                    path=self.path)

        if evolved.line_of_sight(src=evolved.state, dst=state):
            evolved.path = evolved.path_finder.get_path(src=evolved.state, dst=next_state)
            evolved.destination = evolved.state
            evolved.set_direction()

        distance = evolved.distance()
        delta_d = state.distance(next_state)
        while distance < delta_d:
            evolved.state = evolved.destination
            delta_d -= distance
            if evolved.path:
                destination = tlppo.State(values=evolved.path[0])
                evolved.destination = destination
                evolved.set_direction()
                evolved.path = evolved.path[1:]
            else:
                return evolved
            distance = evolved.distance()
        evolved.state = evolved.state.move(evolved.direction, delta_d)
        return evolved


class CellworldParticleFilter(tlppo.ParticleFilter):
    def __init__(self,
                 world: cellworld.World,
                 path_finder: PathFinder):
        self.cell_centers: typing.List[typing.Tuple[float, ...]] = [(cell.location.x, cell.location.y) for cell in world.cells if not cell.occluded]
        self.line_of_sight = LineOfSight(world=world)
        self.path_finder = path_finder
        super().__init__()
        self.history: typing.List[CellworldObservation] = list()
        self.last_observation: typing.Union[CellworldObservation, None] = None
        self.full_view_particle: typing.Union[CellworldParticle, None] = None

    def update_history(self, observation: CellworldObservation) -> None:
        self.history.append(observation)
        self.last_observation = observation
        if self.last_observation.predator:
            self.full_view_particle = CellworldParticle(state=tlppo.State(values=self.last_observation.predator),
                                                        line_of_sight=self.line_of_sight,
                                                        path_finder=self.path_finder)
        else:
            self.full_view_particle = None

    def is_valid(self, particle: CellworldParticle) -> bool:
        last_observation = self.history[-1]
        if self.full_view_particle:
            return False
        else:
            return not self.line_of_sight(src=last_observation.prey, dst=particle.state)

    def new_particle(self) -> CellworldParticle:
        if self.full_view_particle:
            return self.full_view_particle
        else:
            return CellworldParticle(state=tlppo.State(values=random.choice(self.cell_centers)),
                                     line_of_sight=self.line_of_sight,
                                     path_finder=self.path_finder)
