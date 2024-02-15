from matplotlib import pyplot as plt
import numpy as np
import cellworld
import hexaworld
import imageio.v2 as imageio

experiment = cellworld.Experiment.load_from_file("PEEK_20221206_1429_FMM10_21_05_RT8_experiment_pose.json")

world_name = "21_05"
world = cellworld.World.get_from_parameters_names("hexagonal", "canonical", world_name)
line_of_sight = hexaworld.LineOfSight(world)

path_builder = cellworld.Paths_builder.get_from_name("hexagonal", world_name)
paths = cellworld.Paths(builder=path_builder,
                        world=world)


occlusions_polygons = cellworld.Polygon_list.get_polygons(cellworld.Location_list([c.location for c in world.cells.occluded_cells()]),
                                                          6,
                                                          world.implementation.cell_transformation.size / 2 * 1.05,
                                                          world.implementation.cell_transformation.rotation)

visibility = cellworld.Location_visibility(occlusions=occlusions_polygons)

paths_builder = cellworld.Paths_builder.get_from_name("hexagonal", world_name)


def trajectories_to_observations(trajectories: cellworld.Trajectories,
                                 visibility: cellworld.Location_visibility ):
    agent_trajectories = trajectories.split_by_agent()
    predator_trajectory = agent_trajectories["predator"]
    prey_trajectory = agent_trajectories["prey"]
    max_frame = prey_trajectory[-1].frame
    observations = []
    timing = []
    predator_steps = []
    last_time = prey_trajectory[0].time_stamp
    for frame in range(max_frame):
        prey_step = prey_trajectory.get_step_by_frame(frame=frame)
        predator_step = predator_trajectory.get_step_by_frame(frame=frame)
        if prey_step and predator_step:
            if visibility.is_visible(src=prey_step.location, dst=predator_step.location):
                observation = hexaworld.CellworldObservation(prey=prey_step.location,
                                                             predator=predator_step.location)
            else:
                observation = hexaworld.CellworldObservation(prey=prey_step.location,
                                                             predator=None)
            observations.append(observation)
            timing.append(prey_step.time_stamp - last_time)
            predator_steps.append(predator_step)
            last_time = prey_step.time_stamp
    return observations, timing, predator_steps



path_finder = hexaworld.PathFinder(paths=paths,
                                   line_of_sight=line_of_sight)

for episode_number, episode in enumerate(experiment.episodes):
    print("Episode number: %i of %i" % (episode_number, len(experiment.episodes)))
    observations, timing, predator_steps = trajectories_to_observations(trajectories=episode.trajectories,
                                                                        visibility=visibility)

    particle_count = 1000
    belief_state = hexaworld.CellworldBeliefState(world=paths.world,
                                                  path_finder=path_finder,
                                                  size=particle_count,
                                                  attempts=particle_count * 2)
    display = cellworld.Display(world=world)
    particles = []
    for i in range(particle_count):
        particles.append(display.circle(radius=.01,
                                        location=cellworld.Location(0, 0),
                                        color="purple",
                                        alpha=.1))

    with (imageio.get_writer('bs2_episode_%i.gif' % episode_number, mode='I') as writer):
        frame = 0
        for observation, elapsed_time, predator_step in zip(observations, timing, predator_steps):
            belief_state.update_history(observation=observation, delta_t=.002)

            frame += 1
            if frame % 4:
                continue

            for particle in particles:
                particle.set(center=(0, 0),
                             color="white")

            for i, particle in enumerate(belief_state.particles):
                src = belief_state.particles[i].values
                particles[i].set(center=src,
                                 color="purple")
            display.agent(location=cellworld.Location(observation.prey[0],
                                                      observation.prey[1]),
                          rotation=0,
                          color='blue',
                          agent_name='prey')
            display.agent(step=predator_step,
                          color='red', agent_name='predator')
            display.fig.canvas.draw()
            image_from_plot = np.frombuffer(display.fig.canvas.tostring_rgb(), dtype=np.uint8)
            image_from_plot = image_from_plot.reshape(display.fig.canvas.get_width_height()[::-1] + (3,))
            writer.append_data(image_from_plot)
            writer.append_data(image_from_plot)
        plt.close()
