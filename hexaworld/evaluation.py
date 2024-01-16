import tlppo
import typing
from .particle import CellworldParticle


class CellworldEvaluationFunction(tlppo.EvaluationFunction):
    def __init__(self,
                 distance_to_goal_reward: float,
                 distance_to_predator_reward: float,
                 goal_reward: float,
                 goal_radius: float,
                 capture_reward: float,
                 capture_radius: float,
                 goal: typing.Tuple[float, ...]):
        self.distance_to_goal_reward = distance_to_goal_reward
        self.distance_to_predator_reward = distance_to_predator_reward
        self.capture_reward = capture_reward
        self.capture_radius = capture_radius
        self.goal_reward = goal_reward
        self.goal_radius = goal_radius
        self.goal = goal

    def evaluate(self, state: tlppo.State, particle: CellworldParticle) -> typing.Tuple[float, bool]:
        reward: float = 0.0
        _continue = True

        distance_to_goal = state.distance(other=self.goal)
        if self.goal_radius > distance_to_goal:
            reward += self.goal_reward
            _continue = False
        reward += distance_to_goal * self.distance_to_goal_reward

        distance_to_predator = state.distance(other=particle.state)
        if self.capture_radius > distance_to_predator:
            reward += self.capture_reward
            _continue = False
        reward += distance_to_predator * self.distance_to_predator_reward
        return reward, _continue
