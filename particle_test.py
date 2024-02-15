import hexaworld as xw
import tlppo
import cellworld

world_name = "10_00"

world = cellworld.World.get_from_parameters_names("hexagonal", "canonical", world_name)
line_of_sight = xw.LineOfSight(world)

path_builder = cellworld.Paths_builder.get_from_name("hexagonal", world_name)
paths = cellworld.Paths(builder=path_builder,
                        world=world)

path_finder = xw.PathFinder(paths=paths,
                            line_of_sight=line_of_sight)

particle = xw.CellworldParticle(values=(0.5, 0.5),
                                line_of_sight=line_of_sight,
                                path_finder=path_finder)

state = tlppo.State(values=(0, 0.5))
next_state = tlppo.State(values=(1, 0.5))

evolved = particle.project(state=state, next_state=next_state)


evaluation_function = xw.CellworldEvaluationFunction(distance_to_goal_reward=0.0,
                                                     distance_to_predator_reward=-0.0,
                                                     goal_reward=10.0,
                                                     goal_radius=.07,
                                                     capture_reward=-10.0,
                                                     capture_radius=.07,
                                                     goal=(1.0, .5))

print(evolved.values)
print(evaluation_function.evaluate(state=next_state, particle=evolved))

