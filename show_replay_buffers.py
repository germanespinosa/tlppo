import numpy as np
import math
import botevade
import cellworld
import hexaworld
import tlppo
from loader import Loader
import imageio.v2 as imageio
import matplotlib.pyplot as plt

world_name = "10_03"

world = cellworld.World.get_from_parameters_names("hexagonal", "canonical", world_name)

sources, destinations = Loader.load_files("%s/dreamer*.h5" % world_name)


display = cellworld.Display(world=world)


trajectory = cellworld.Trajectories()
time_stamp = 0
last_location = cellworld.Location(sources[0][0], sources[0][1])
for frame, src in enumerate(sources):
    location = cellworld.Location(src[0],src[1])
    step = cellworld.Step(time_stamp=time_stamp,
                          agent_name="prey",
                          frame=frame, location=location)
    if last_location.dist(location=location) > .1:
        time_stamp = 0
        display.add_trajectories(trajectories=trajectory, alphas={"prey": .1})
        trajectory.clear()
    last_location = location
    time_stamp += .01
    trajectory.append(step)

sources, destinations = Loader.load_files("%s/SAC*.h5" % world_name)



trajectory = cellworld.Trajectories()
time_stamp = 0
last_location = cellworld.Location(sources[0][0], sources[0][1])
for frame, src in enumerate(sources):
    location = cellworld.Location(src[0],src[1])
    step = cellworld.Step(time_stamp=time_stamp,
                          agent_name="prey",
                          frame=frame, location=location)
    if last_location.dist(location=location) > .1:
        time_stamp = 0
        display.add_trajectories(trajectories=trajectory, colors={"prey":"red"}, alphas={"prey": .1})
        trajectory.clear()
    last_location = location
    time_stamp += .01
    trajectory.append(step)


plt.show()
