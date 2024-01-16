import math
import botevade
import cellworld
import hexaworld
import tlppo
from loader import Loader

world_name = "10_03"
sources, destinations = Loader.load_files("%s/*.csv" % world_name)

world = cellworld.World.get_from_parameters_names("hexagonal", "canonical", world_name)
line_of_sight = hexaworld.LineOfSight(world)

graph = Loader.create_graph(sources=sources,
                            destinations=destinations,
                            state_count=100,
                            line_of_sight=line_of_sight)

tlppo_graph, lppo = Loader.create_lppo_graph(graph=graph,
                                             lppo_count=20,
                                             depth=1)

path_builder = cellworld.Paths_builder.get_from_name("hexagonal", world_name)

paths = cellworld.Paths(builder=path_builder,
                        world=world)

particle_filter = Loader.create_particle_filter(paths=paths,
                                                line_of_sight=line_of_sight)
belief_state = tlppo.BeliefState(size=100,
                                 particle_filter=particle_filter)

evaluation_function = hexaworld.CellworldEvaluationFunction(distance_to_goal_reward=1.0,
                                                            distance_to_predator_reward=-1.0,
                                                            goal_reward=10.0,
                                                            goal_radius=.06,
                                                            capture_reward=10.0,
                                                            capture_radius=.06,
                                                            goal=(1.0, .5))



#creates the environment


occlusions_polygons = cellworld.Polygon_list.get_polygons(cellworld.Location_list([c.location for c in world.cells.occluded_cells()]),
                                                          6,
                                                          world.implementation.cell_transformation.size / 2 * 1.05,
                                                          world.implementation.cell_transformation.rotation)

visibility = cellworld.Location_visibility(occlusions=occlusions_polygons)


paths_builder = cellworld.Paths_builder.get_from_name("hexagonal", world_name)

prey_agent = botevade.SelfDrivenAgent(agent_name="prey",
                                      pworld=world,
                                      ppath_builder=paths_builder,
                                      pvisibility=visibility,
                                      pP_value=2,
                                      pI_value=0,
                                      pD_value=0,
                                      pmax_speed=1.5,
                                      pmax_turning_speed=math.pi)


e = botevade.Environment(world_name,
                         freq=100,
                         has_predator=True,
                         real_time=False,
                         prey_agent=prey_agent)

counter = 0
planner = tlppo.Planner(evaluation_function=evaluation_function)
for i in range(10):
    e.start()
    while not e.complete:
        e.step()
        if counter % 3 == 0:
            post_o = e.get_observation()
            observation = hexaworld.CellworldObservation(prey=post_o[0], predator=post_o[3])
            belief_state.filter(observation=observation)
            belief_state.complete(attempts=100)
            tree = Loader.create_tree(graph=tlppo_graph, values=observation.prey, line_of_sight=line_of_sight)
            target_state = planner.get_action(tree=tree, belief_state=belief_state)
            cell_id = world.cells.find(cellworld.Location(target_state.values[0], target_state.values[1]))
            prey_agent.set_destination_cell(destination_cell=world.cells[cell_id])
        e.show()
        counter += 1
    e.stop()

# return prey.location, \
#     prey.theta, \
#     self.goal_location, \
#     predator.location, \
#     predator.theta, \
#     captured, \
#     goal_reached, \
#     closest_occlusions