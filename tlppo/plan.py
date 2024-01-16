from .mcts import Tree
from .state import State
from .evaluation import EvaluationFunction
from .particle import BeliefState


class Planner:
    def __init__(self,
                 evaluation_function: EvaluationFunction,
                 depth: int = 10,
                 iterations: int = 10):
        self.evaluation_function: EvaluationFunction = evaluation_function
        self.depth = depth
        self.iterations = iterations

    def get_action(self,
                   tree: Tree,
                   belief_state: BeliefState,
                   depth: int = -1,
                   iterations: int = -1) -> State:
        if depth == -1:
            depth = self.depth
        if iterations == -1:
            iterations = self.iterations
        for i in range(iterations):
            node = tree.root
            reward = 0
            particle = belief_state.get_particle()
            state = node.state
            for d in range(depth):
                node = node.select(c=0.5)
                next_state = node.state
                particle = particle.evolve(state=state, next_state=next_state)
                state = next_state
                state_reward, _continue = self.evaluation_function.evaluate(state=state, particle=particle)
                reward += state_reward
                if not _continue:
                    break
            node.propagate_reward(reward=reward)
        return tree.root.select(0).state


