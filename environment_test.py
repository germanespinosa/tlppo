import numpy as np
import math
import botevade
import cellworld
import hexaworld
import tlppo
from loader import Loader
import imageio.v2 as imageio

world_name = "10_03"

world = cellworld.World.get_from_parameters_names("hexagonal", "canonical", world_name)
line_of_sight = hexaworld.LineOfSight(world)


sources, destinations = Loader.load_files("%s/*.csv" % world_name)
graph = Loader.create_graph(sources=sources,
                            destinations=destinations,
                            state_count=100,
                            line_of_sight=line_of_sight)

tlppo_graph, lppo = Loader.create_lppo_graph(graph=graph,
                                             lppo_count=40,
                                             depth=1)

# graph = Loader.create_spatial_graph(world=world)
# lppo = [0,1,2,4,13,18,20,24,36,46,57,92,136,137,154,155,158,162,163,179,186,190,194,231,232,239,240,244,254,255,260,265,270,275,276,278,279,285,299,330]
# tlppo_graph = graph.get_subgraph(nodes=lppo)


path_builder = cellworld.Paths_builder.get_from_name("hexagonal", world_name)
paths = cellworld.Paths(builder=path_builder,
                        world=world)

evaluation_function = hexaworld.CellworldEvaluationFunction(distance_to_goal_reward=1.0,
                                                            distance_to_predator_reward=-1.0,
                                                            goal_reward=10.0,
                                                            goal_radius=.07,
                                                            capture_reward=-10.0,
                                                            capture_radius=.07,
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
                                      pP_value=6,
                                      pI_value=0,
                                      pD_value=0,
                                      pmax_speed=1.5,
                                      pmax_turning_speed=math.pi)

e = botevade.Environment(world_name,
                         freq=100,
                         has_predator=True,
                         real_time=False,
                         prey_agent=prey_agent)

planner = tlppo.Planner(evaluation_function=evaluation_function,
                        depth=10,
                        iterations=1000)

destination = e.model.display.circle(radius=.02,
                                     location=hexaworld.to_location((0, 0)),
                                     color="purple",
                                     alpha=.3)


# show graph
# for label, node in tlppo_graph.nodes.items():
#     for edge in tlppo_graph.edges[label]:
#         conn = tlppo_graph.nodes[edge]
#         e.model.display.line(beginning=hexaworld.to_location(node.state.values),
#                              ending=hexaworld.to_location(conn.state.values),
#                              color="green", alpha=.1)


particle_count = 100
particles = []
particles_arrows = []

for i in range(particle_count):
    particles.append(e.model.display.circle(radius=.01,
                                            location=cellworld.Location(0, 0),
                                            color="red",
                                            alpha=.2))
    particles_arrows.append(e.model.display.arrow(beginning=cellworld.Location(0, 0),
                                                  ending=cellworld.Location(0, 0),
                                                  color="red",
                                                  alpha=.2))

path_finder = hexaworld.PathFinder(paths=paths,
                                   line_of_sight=line_of_sight)

target_state = tlppo.State(values=(0, 0))

for i in range(10):
    belief_state = hexaworld.CellworldBeliefState(world=paths.world,
                                                  path_finder=path_finder,
                                                  size=100,
                                                  attempts=100)

    e.start()
    counter = 0
    observed_predator = False
    with (imageio.get_writer('episode_%i.gif' % i, mode='I') as writer):
        while not e.complete:
            e.step()
            post_o = e.get_observation()
            observation = hexaworld.CellworldObservation(prey=post_o[0],
                                                         predator=post_o[3])
            belief_state.update_history(observation=observation)
            for particle, arrow in zip(particles, particles_arrows):
                particle.set(center=(0, 0),
                             color="white")
                arrow.set_color("white")
                arrow.set_data(x=0, y=0, dx=0, dy=0)

            for i, particle in enumerate(belief_state.particles):
                src = belief_state.particles[i].values
                particles[i].set(center=src,
                                 color="red")
                dst = particle.path[-1] if particle.path else src
                particles_arrows[i].set_color("red")
                particles_arrows[i].set_data(x=src[0], y=src[1], dx=dst[0]-src[0], dy=dst[1]-src[1])
                # else:
                #     particles[i].set(center=(0, 0),
                #                      color="white")
                #     particles_arrows[i].set_color("white")
                #     particles_arrows[i].set_data(x=0, y=0, dx=0, dy=0)

            if (observation.predator and not observed_predator) or counter % 30 == 0 or tlppo.distance(observation.prey, target_state.values) < .02:
                counter = 0
                tree = Loader.create_tree(graph=tlppo_graph,
                                          values=observation.prey,
                                          line_of_sight=line_of_sight)

                target_state = planner.get_action(tree=tree,
                                                  belief_state=belief_state,
                                                  discount=0)
                Loader.clear_tree(display=e.model.display)
                print(max([(node.value/node.visits) for node in tree.root.children if node.visits]),
                      max([node.visits for node in tree.root.children if node.visits]),
                      min([node.visits for node in tree.root.children if node.visits]))
                Loader.plot_tree(tree=tree, display=e.model.display)
                cell_id = world.cells.find(cellworld.Location(target_state.values[0], target_state.values[1]))
                destination.set(center=target_state.values,
                                color="b")
                prey_agent.set_destination_cell(destination_cell=world.cells[cell_id])

            observed_predator = observation.predator

            e.show()

            counter += 1
            #plt.savefig("frame.png")
            # with io.BytesIO() as buffer:
            #     plt.savefig(buffer, format='png')
#            image = imageio.imread("frame.png")
#             buffer.seek(0)
            e.model.display.fig.canvas.draw()
            image_from_plot = np.frombuffer(e.model.display.fig.canvas.tostring_rgb(), dtype=np.uint8)
            image_from_plot = image_from_plot.reshape(e.model.display.fig.canvas.get_width_height()[::-1] + (3,))
            writer.append_data(image_from_plot)
            writer.append_data(image_from_plot)

    e.stop()

