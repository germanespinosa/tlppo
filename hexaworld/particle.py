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
                 values: typing.Tuple[float, ...],
                 line_of_sight: LineOfSight,
                 path_finder: PathFinder,
                 path: typing.List[typing.Tuple[float, ...]] = None,
                 ratio: float = -1):
        self.values = values
        self.line_of_sight = line_of_sight
        self.direction = None
        self.path: typing.List[typing.Tuple[float, ...]]
        if path is not None:
            self.path = path
        else:
            self.path = []
        self.path_finder: PathFinder = path_finder
        if ratio == -1:
            self.ratio = .5 + random.random()
        else:
            self.ratio = ratio
        self.speed = 0.5

    def copy(self, with_path: bool = False) -> "CellworldParticle":
        new_particle = CellworldParticle(values=self.values,
                                         line_of_sight=self.line_of_sight,
                                         path_finder=self.path_finder)
        if with_path:
            new_particle.path = [step for step in self.path]
        return new_particle

    def noisy_copy(self, noise: float = .02):
        new_particle = CellworldParticle(values=tlppo.noisy_copy(src=self.values, noise=noise),
                                         line_of_sight=self.line_of_sight,
                                         path_finder=self.path_finder)
        new_particle.speed = self.speed + 2 * noise * random.random() - noise
        new_particle.path = [step for step in self.path]
        return new_particle

    def evolve(self,
               delta_t: float):

        delta_d = delta_t * self.speed * self.ratio

        if not self.path:
            self.path = self.path_finder.get_random_path(self.values)

        distance = tlppo.distance(self.values, self.path[0])

        while distance < delta_d:
            self.values = self.path[0]
            self.path = self.path[1:]
            if not self.path:
                self.path = self.path_finder.get_random_path(self.values)
            delta_d -= distance
            distance = tlppo.distance(self.values, self.path[0])

        if delta_d > 0:
            self.values = tlppo.move(self.values, self.path[0], delta_d)

    def project(self,
                state: tlppo.State,
                next_state: tlppo.State) -> "CellworldParticle":

        evolved = CellworldParticle(values=self.values,
                                    line_of_sight=self.line_of_sight,
                                    path_finder=self.path_finder,
                                    path=self.path,
                                    ratio=self.ratio)

        los = evolved.line_of_sight(src=evolved.values, dst=state.values)

        if los:
            evolved.path = evolved.path_finder.get_path(src=evolved.values, dst=next_state.values)

        delta_d = state.distance(next_state) * self.ratio

        if not evolved.path:
            evolved.path = evolved.path_finder.get_random_path(evolved.values)

        distance = tlppo.distance(evolved.values, evolved.path[0])

        while distance < delta_d:
            evolved.values = evolved.path[0]
            evolved.path = evolved.path[1:]
            delta_d -= distance
            if not evolved.path:
                if los:
                    return evolved
                else:
                    evolved.path = evolved.path_finder.get_random_path(evolved.values)
            distance = tlppo.distance(evolved.values, evolved.path[0])

        if delta_d:
            evolved.values = tlppo.move(evolved.values, evolved.path[0], delta_d)
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
        self.last_predator = None

    def update_history(self, observation: CellworldObservation, delta_t: float=.01) -> None:
        if observation.predator:
            self.last_predator = observation.predator
            self.particles.clear()
            self.particles.append(CellworldParticle(values=observation.predator,
                                                    line_of_sight=self.line_of_sight,
                                                    path_finder=self.path_finder,
                                                    path=[observation.prey]))
        else:
            if self.last_predator:
                for _ in range(self.attempts):
                    if len(self.particles) >= self.size:
                        break
                    candidate_particle: CellworldParticle = self.particles[0].noisy_copy(noise=.025)
                    if not self.line_of_sight.is_valid(candidate_particle.values):
                        continue
                    if not self.line_of_sight(src=candidate_particle.values, dst=self.last_predator):
                        candidate_particle.path = []
                    if random.random() < .5:
                        candidate_particle.path = []
                    self.particles.append(candidate_particle)

            if self.history:
                for particle in self.particles:
                    particle.evolve(delta_t=delta_t)
            filtered: typing.List[CellworldParticle] = list()
            for particle in self.particles:
                if not self.line_of_sight(observation.prey, particle.values):
                    filtered.append(particle)
            self.particles = filtered
            if self.particles:
                for _ in range(self.attempts):
                    if len(self.particles) >= self.size:
                        break
                    candidate_particle: CellworldParticle = random.choice(self.particles).copy(with_path=self.last_predator is not None)
                    self.particles.append(candidate_particle)
            else:
                for _ in range(self.attempts):
                    if len(self.particles) >= self.size:
                        break
                    candidate = random.choice(self.cell_centers)
                    if not self.line_of_sight(observation.prey, candidate):
                        self.particles.append(CellworldParticle(values=candidate,
                                                                line_of_sight=self.line_of_sight,
                                                                path_finder=self.path_finder))
            self.last_predator = None
        tlppo.BeliefState.update_history(self, observation=observation)

