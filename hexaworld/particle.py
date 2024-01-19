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


class CellworldBeliefState(tlppo.BeliefState):
    def __init__(self,
                 world: cellworld.World,
                 path_finder: PathFinder,
                 size: int = 100,
                 attempts: int = 200):
        self.cell_centers: typing.List[typing.Tuple[float, ...]] = [(cell.location.x, cell.location.y) for cell in world.cells if not cell.occluded]
        self.line_of_sight = LineOfSight(world=world)
        self.path_finder = path_finder
        self.size = size
        self.attempts = attempts
        super().__init__()
        self.history: typing.List[CellworldObservation] = list()
        self.particles: typing.List[CellworldParticle] = list()
        self.full_view_particle = None

    def update_history(self, observation: CellworldObservation) -> None:
        if observation.predator:
            self.particles.clear()
            for i in range(self.size):
                self.particles.append(CellworldParticle(state=tlppo.State(values=observation.predator),
                                                        line_of_sight=self.line_of_sight,
                                                        path_finder=self.path_finder,
                                                        path=[observation.prey]))
        else:
            self.full_view_particle = None
            if self.history:
                for i in range(len(self.particles)):
                    self.particles[i] = self.particles[i].evolve(state=tlppo.State(self.history[-1].prey),
                                                                 next_state=tlppo.State(observation.prey))
            filtered: typing.List[CellworldParticle] = list()
            for particle in self.particles:
                if not self.line_of_sight(observation.prey, particle.state):
                    filtered.append(particle)
            self.particles = filtered
            for a in range(self.attempts):
                candidate = random.choice(self.cell_centers)
                if not self.line_of_sight(observation.prey, candidate):
                    self.particles.append(CellworldParticle(state=tlppo.State(values=candidate),
                                                            line_of_sight=self.line_of_sight,
                                                            path_finder=self.path_finder))
                if len(self.particles) >= self.size:
                    break
        tlppo.BeliefState.update_history(self, observation=observation)