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

# graph = Loader.create_graph(sources=sources,
#                             destinations=destinations,
#                             state_count=100,
#                             line_of_sight=line_of_sight)

graph = Loader.create_spatial_graph(world=world)

lppo = [0,1,2,4,13,18,20,24,36,46,57,92,136,137,154,155,158,162,163,179,186,190,194,231,232,239,240,244,254,255,260,265,270,275,276,278,279,285,299,330]

tlppo_graph = graph.get_subgraph(nodes=lppo)

# tlppo_graph, lppo = Loader.create_lppo_graph(graph=graph,
#                                              lppo_count=40,
#                                              depth=1)

path_builder = cellworld.Paths_builder.get_from_name("hexagonal", world_name)
paths = cellworld.Paths(builder=path_builder,
                        world=world)

belief_state = Loader.create_belief_state(paths=paths,
                                          line_of_sight=line_of_sight)

evaluation_function = hexaworld.CellworldEvaluationFunction(distance_to_goal_reward=1.0,
                                                            distance_to_predator_reward=-1.0,
                                                            goal_reward=10.0,
                                                            goal_radius=.06,
                                                            capture_reward=-10.0,
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
                                      pP_value=4,
                                      pI_value=0,
                                      pD_value=0,
                                      pmax_speed=1.5 * 8,
                                      pmax_turning_speed=math.pi * 4)

e = botevade.Environment(world_name,
                         freq=100,
                         has_predator=True,
                         real_time=False,
                         prey_agent=prey_agent)

counter = 0
planner = tlppo.Planner(evaluation_function=evaluation_function, depth=5, iterations=30)

destination = e.model.display.circle(radius=.02,
                                     location=hexaworld.to_location((0, 0)),
                                     color="purple",
                                     alpha=.3)

for l in lppo:
    e.model.display.circle(radius=.01, location=world.cells[l].location, color="yellow", alpha=.5)

particle_count = 100
particles = []

for i in range(particle_count):
    particles.append(e.model.display.circle(radius=.01, location=cellworld.Location(0, 0), color="red", alpha=.5))


for i in range(10):
    e.start()
    while not e.complete:
        e.step()
        if counter % 1 == 0:
            post_o = e.get_observation()
            observation = hexaworld.CellworldObservation(prey=post_o[0],
                                                         predator=post_o[3])
            belief_state.update_history(observation=observation)
            for i in range(particle_count):
                if i < len(belief_state.particles):
                    particles[i].set(center=belief_state.particles[i].state.values)
                else:
                    particles[i].set(center=(0, 0))

            tree = Loader.create_tree(graph=tlppo_graph,
                                      values=observation.prey,
                                      line_of_sight=line_of_sight)
            target_state = planner.get_action(tree=tree,
                                              belief_state=belief_state)
            cell_id = world.cells.find(cellworld.Location(target_state.values[0], target_state.values[1]))
            destination.set(center=(target_state.values),
                            color="b")
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
