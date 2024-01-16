import typing
from tlppo.state import State
import random


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
