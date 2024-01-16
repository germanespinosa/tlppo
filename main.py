import os.path
import pickle
import cellworld
from tlppo import *
from hexaworld import CellworldParticleFilter, PathFinder

world_name = "10_03"

State.set_dimensions(dimension_count=5)
state = State(values=(.5, .5, .5, .5, .5))
state_path = [(0.0, 1.0, .75, 1.0, .25), (1.0, .40, .55, .6, .5)]
particle = Particle(state=state)
particle.path = state_path

print(particle.state.values, particle.destination.values)
for i in range(50):
    particle = particle.evolve(delta_d=.1)
    print(i, particle.state.values)

State.set_dimensions(dimension_count=2)

world = cellworld.World.get_from_parameters_names("hexagonal", "canonical", world_name)
path_builder = cellworld.Paths_builder.get_from_name("hexagonal", world_name)
paths = cellworld.Paths(builder=path_builder, world=world)
processed_paths_file_path = "processed_paths_%s" % world_name
if os.path.exists(processed_paths_file_path):
    with open(processed_paths_file_path, 'rb') as f:
        processed_paths = pickle.load(f)
else:
    processed_paths = PathFinder.generate_paths(world=world, paths=paths)
    with open(processed_paths_file_path, 'wb') as f:
        pickle.dump(processed_paths, f)

path_finder = PathFinder(processed_paths=processed_paths)

particle_source = CellworldParticleFilter(world=world, path_finder=path_finder)

for i in range(20):
    particle = particle_source.get_particle()
    print(particle.state.values)

for i in range(20):
    src = particle_source.get_particle().state.values
    dst = particle_source.get_particle().state.values
    while los.is_visible(src=src, dst=dst):
        dst = particle_source.get_particle().state.values


    path = path_finder.get_path(src=src, dst=dst)
    particle = Particle(state=State(values=src))
    particle.path = path

    while particle.state.values != dst:
        print(particle.state.values)
        particle.evolve(delta_d=.001)
    print(particle.state.values)
    print(path)


predator_model = PredatorModel(speed_ratio=.35,
                               destinations=particle_source.cell_centers,
                               path_finder=path_finder,
                               line_of_sight=los)

print("destination:")
print(predator_model.exploration_destination(observer=[.3, .2]))
exit()

import csv
import json


def read_csv(filename):
    with open(filename, newline='') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',', quotechar='"')
        columns = []
        items = []
        for row in spamreader:
            if columns:
                items.append({k: json.loads(v) for k, v in zip(columns, row)})
                # items.append([json.loads(v) for v in row])
            else:
                columns = row

        return columns, items


columns, items = read_csv('.\\10_03\\ICM10_03_5w.csv')


import glob
from cellworld import Display, World
import h5py
import pandas as pd
from tlppo import *


def read(file_path):
    with h5py.File(file_path, 'r') as f:
        state = f['state'][:]
        action = f['action'][:]
        next_state = f['next_state'][:]
        reward = f['reward'][:]
        done = f['done'][:]
    df = pd.DataFrame({
        'state': state.tolist(),  # Converting arrays to lists for DataFrame compatibility
        'action': action.tolist(),
        'next_state': next_state.tolist(),
        'reward': reward.tolist(),
        'done': done.tolist()
    })
    return df


sources: typing.List[typing.Tuple[float]] = list()
destinations: typing.List[typing.Tuple[float]] = list()

# for file_path in glob.glob("10_03/*.h5"):
#     replay = read(file_path)
#     for index, row in replay.iterrows():
#         sources.append(tuple(row['state'][:2]))
#         destinations.append(tuple(row['next_state'][:2]))

for file_path in glob.glob("10_03/*.csv"):
    columns, replay = read_csv(file_path)
    for row in replay:
        sources.append(tuple(row['state'][:2]))
        destinations.append(tuple(row['next_state'][:2]))



depth = 1
state_count = 100
lppo_count = 20

clusters = Clusters(data_points=sources+destinations, cluster_count=state_count)

source_labels = clusters.get_labels(sources)
destination_labels = clusters.get_labels(destinations)

graph = Graph()
for values in clusters.centroids:
    graph.add_node(state=State(values=values))

for source_label, destination_label in zip(source_labels, destination_labels):
    if source_label == destination_label:
        continue
    graph.connect(src_label=source_label, dst_label=destination_label)

w = World.get_from_parameters_names("hexagonal", "canonical", "10_03")
lppo = graph.get_lppo(n=lppo_count, depth=depth)

# d = Display(w)
centrality = graph.get_centrality(depth=depth)
colors = get_color_map(list(centrality.values()))
# draw_graph(d, graph=graph, colors=colors)
# draw_lppo(d, graph=graph, lppo=lppo)
# plt.show()

tlppo_graph = graph.get_subgraph(nodes=lppo)

# d = Display(w)
# draw_graph(d, graph=tlppo_graph)
# draw_lppo(d, graph=graph, lppo=lppo)
# plt.show()

for src_label, src_node in tlppo_graph.nodes.items():
    for dst_label, dst_node in tlppo_graph.nodes.items():
        if dst_label in tlppo_graph.edges[src_label]:
            print(src_label, "-", dst_label, ": ", end="")
            print(tlppo_graph.edges[src_label][dst_label])

d = Display(w)
draw_graph(d, graph=graph)
draw_lppo(d, graph=graph, lppo=lppo)
plt.show()

goal_state = State(values=(1.0, .5))
goal_node = tlppo_graph.add_node(state=goal_state)
for label in lppo:
    tlppo_graph.connect(src_label=label, dst_label=goal_node.label)

tree = Tree(graph=tlppo_graph, values=(0.0, .5))


depth = 10
for i in range(10):
    node = tree.root
    reward = 0
    for j in range(depth):
        node = node.select(c=0.5)
        reward += (1 - node.state.distance([1.0, .5])) * (1/depth)
    node.propagate_reward(reward=reward)

tree.root.print()
d = Display(w)
draw_tree(d=d, tree=tree)
plt.show()
