from hexaworld.hexa_world import *
from loader import Loader

sources, destinations = Loader.load_files("10_03/*.csv")

graph = Loader.create_graph(sources=sources, destinations=destinations, state_count=100)

tlppo_graph = Loader.create_lppo_graph(graph=graph, lppo_count=20, depth=1)

particle_filter = Loader.create_particle_filter("10_03")
belief_state = BeliefState(size=100, particle_filter=particle_filter)
planner = Planner(graph=tlppo_graph, belief_state=belief_state)
print(graph, tlppo_graph)


from botevade import Environment
from cellworld import *

#creates the environment

e = Environment("10_03", freq=100, has_predator=True, real_time=True)

counter = 0
for i in range(10):
    e.start()

    while not e.complete:
        t = Timer()
        pre_o = e.get_observation()
        observation = CellworldObservation(pre_o[0], pre_o[3])
        belief_state.filter()
        e.set_action(.1, .1)

        e.step()
        post_o = e.get_observation()
        counter += 1
        if counter % 3 == 0:
            e.show()
            print(pre_o, post_o)
        #computes the remaining time for 1/10 of a second to make the action interval consistent.
        # observation format: Tuple
        # [prey location, prey theta, goal location, predator location, predator theta, captured, goal_reached]
        # prey location: Type Location
        # prey theta: Type float in radians
        # goal location: Type Location
        # predator location: Type Location (None when predator is not visible)
        # predator theta: Type float in radians (None when predator is not visible)
        # captured: Type boolean : Prey has been captured by the predator. environment.complete becomes true.
        # goal_reached : Type boolean : Prey reached the goal location. environment.complete becomes true.

    #stops the environment
    e.stop()

