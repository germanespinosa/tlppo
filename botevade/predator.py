import math
import random
import cellworld as cw
from .agent import AgentAction, SelfDrivenAgent


class Predator(SelfDrivenAgent):
    def __init__(self,
                 pworld: cw.World,
                 ppath_builder: cw.Paths_builder,
                 pvisibility: cw.Location_visibility,
                 pP_value: float = .1,
                 pI_value: float = .1,
                 pD_value: float = .1,
                 pmax_speed: float = .4,
                 pmax_turning_speed: float = .2):
        SelfDrivenAgent.__init__(self,
                                 agent_name="predator",
                                 pworld=pworld,
                                 ppath_builder=ppath_builder,
                                 pvisibility=pvisibility,
                                 pP_value=pP_value,
                                 pI_value=pI_value,
                                 pD_value=pD_value,
                                 pmax_speed=pmax_speed,
                                 pmax_turning_speed=pmax_turning_speed)

    def get_action(self, observation: dict) -> AgentAction:
        prey = observation["prey"]
        predator = observation["predator"]

        if prey:
            self.destination_cell = self.world.cells[self.world.cells.find(prey.location)]

        if self.destination_cell is None:
            hidden_cells = cw.Cell_group()
            for c in self.world.cells:
                if c.occluded:
                    continue
                if not self.visibility.is_visible(predator.location, c.location):
                    hidden_cells.append(c)
            self.destination_cell = random.choice(hidden_cells)

        return SelfDrivenAgent.get_action(self, observation=observation)
