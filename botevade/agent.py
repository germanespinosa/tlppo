import math
import cellworld as cw
import json_cpp


class AgentAction(json_cpp.JsonObject):
    def __init__(self, speed: float = 0, turning_speed: float = 0):
        self.speed = speed
        self.turning_speed = turning_speed*10
        super().__init__()


class AgentData(json_cpp.JsonObject):

    def __init__(self,
                 plocation: cw.Location,
                 ptheta: float,
                 pspeed: float,
                 pturning_speed: float,
                 pcolor: str = "b",
                 pauto_update=True):
        self.location = plocation
        self.theta = ptheta
        self.speed = pspeed
        self.turning_speed = pturning_speed
        self.color = pcolor
        self.auto_update = pauto_update
        super().__init__()


class Agent(object):

    def start(self) -> None:
        pass

    def get_action(self, observation: dict) -> AgentAction:
        return AgentAction(0, 0)


class SelfDrivenAgent(Agent):

    def __init__(self,
                 agent_name: str,
                 pworld: cw.World,
                 ppath_builder: cw.Paths_builder,
                 pvisibility: cw.Location_visibility,
                 pP_value: float = .1,
                 pI_value: float = .1,
                 pD_value: float = .1,
                 pmax_speed: float = .4,
                 pmax_turning_speed: float = .2):
        self.agent_name = agent_name
        self.world = pworld
        self.paths = cw.Paths(ppath_builder, pworld)
        self.visibility = pvisibility
        self.P_value = pP_value
        self.I_value = pI_value
        self.D_value = pD_value
        self.max_speed = pmax_speed
        self.max_turning_speed = pmax_turning_speed
        self.destination = None
        self.destination_cell = None
        self.last_theta = None
        self.accum_theta_error = 0
        self.path = None

    def start(self) -> None:
        print("starting")
        self.destination = None
        self.last_theta = None
        self.accum_theta_error = 0
        self.path = None

    def set_destination_cell(self,
                             destination_cell: cw.Cell) -> None:
        self.destination_cell = destination_cell

    @staticmethod
    def normalized_error(theta_error: float) -> float:
        pi_err = math.pi * theta_error / 2
        return 1 / (pi_err * pi_err + 1)

    def get_action(self,
                   observation: dict) -> AgentAction:
        agent_data = observation[self.agent_name]

        if self.destination_cell and \
                agent_data.location.dist(self.destination_cell.location) < self.world.implementation.cell_transformation.size / 4:
            self.destination_cell = None

        agent_cell = self.world.cells[self.world.cells.find(agent_data.location)]

        if self.destination_cell is not None:
            self.path = self.paths.get_path(agent_cell, self.destination_cell)
            for cd in self.path:
                if self.visibility.is_visible(agent_data.location, cd.location):
                    self.destination = cd.location

        if not self.destination:
            return AgentAction(speed=0, turning_speed=0)

        desired_theta = agent_data.location.atan(self.destination)
        theta_error, direction = cw.angle_difference(agent_data.theta, desired_theta)
        dist_error = agent_data.location.dist(self.destination)
        self.accum_theta_error += theta_error
        turning_speed_P = theta_error * self.P_value
        turning_speed_D = 0
        if self.last_theta is not None:
            turning_speed_D = (self.last_theta - agent_data.theta) * self.D_value
        turning_speed_I = self.accum_theta_error * self.I_value
        turning_speed = turning_speed_P - turning_speed_D + turning_speed_I
        if turning_speed > self.max_turning_speed:
            turning_speed = self.max_turning_speed
        turning_speed = turning_speed * (-direction)
        speed = self.normalized_error(theta_error) * (1 + dist_error)
        if speed > self.max_speed:
            speed = self.max_speed
        self.last_theta = agent_data.theta
        return AgentAction(speed=speed, turning_speed=turning_speed)
