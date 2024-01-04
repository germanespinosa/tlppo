import pickle
# Load the replay buffer
with open('10_03/10_03_5w.pkl', 'rb') as file:
    replay_buffer = pickle.load(file)
observations = replay_buffer.observations
actions = replay_buffer.actions
rewards = replay_buffer.rewards
next_observations = replay_buffer.next_observations
dones = replay_buffer.dones
print(observations.shape)

exit()


import glob
from cellworld import Display, Location, World
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

for file_path in glob.glob("10_03/*.h5"):
    replay = read(file_path)
    for index, row in replay.iterrows():
        sources.append(tuple(row['state'][:2]))
        destinations.append(tuple(row['next_state'][:2]))


depth = 1
state_count = 100
lppo_count = 10

clusters = Clusters(data_points=sources+destinations, cluster_count=state_count)

source_labels = clusters.get_labels(sources)
destination_labels = clusters.get_labels(destinations)


def draw_graph(display: Display, graph: Graph, colors=None):
    if colors is None:
        colors = ["grey" for _ in graph.nodes]
    min_line_width = 0.001
    max_line_width = 0.003
    min_cost = .03  # min([min(costs.values()) for label, costs in graph.costs.items() if costs])
    max_cost = .1  # max([max(costs.values()) for label, costs in graph.costs.items() if costs])

    def line_width(cost):
        r = (cost - min_cost) / (max_cost - min_cost)
        return min_line_width + r * max_line_width

    for (label, node), node_color in zip(graph.nodes.items(), colors):
        node_location = Location(node.state.values[0], node.state.values[1])
        display.circle(node_location, color=node_color, radius=.02)
        plt.text(node_location.x, node_location.y, str(label), zorder=10)
        for connection_label in graph.edges[label]:
            src_location = node_location
            src_node = node
            dst_location = Location()
            for dst_label in graph.edges[label][connection_label]:
                dst_node = graph[dst_label]
                dst_location = Location(dst_node.state.values[0], dst_node.state.values[1])
                cost = src_node.state.distance(dst_node.state.values)
                width = line_width(cost)
                d.arrow(src_location, dst_location, color="orange", head_width=width * 2, line_width=width)
                src_location = dst_location
                src_node = dst_node
            cost = graph.costs[label][connection_label]
            width = line_width(cost)
            d.arrow(node_location, dst_location, color="blue", head_width=width * 2, line_width=width, alpha=.5)


def draw_lppo(display: Display, graph: Graph, lppo: typing.List[int]):
    for label in lppo:
        node = graph.nodes[label]
        node_location = Location(node.state.values[0], node.state.values[1])
        display.circle(node_location, color="green", radius=.02)


graph = Graph()
for values in clusters.centroids:
    graph.add_node(state=State(values=values))

for source_label, destination_label in zip(source_labels, destination_labels):
    if source_label == destination_label:
        continue
    graph.connect(src_label=source_label, dst_label=destination_label)

w = World.get_from_parameters_names("hexagonal", "canonical", "10_03")
lppo = graph.get_lppo(n=lppo_count, depth=depth)

d = Display(w)
centrality = graph.get_centrality(depth=depth)
colors = get_color_map(list(centrality.values()))
draw_graph(d, graph=graph, colors=colors)
draw_lppo(d, graph=graph, lppo=lppo)
plt.show()

tlppo_graph = graph.get_subgraph(nodes=lppo)

d = Display(w)
draw_graph(d, graph=tlppo_graph)
draw_lppo(d, graph=graph, lppo=lppo)
plt.show()

for src_label, src_node in tlppo_graph.nodes.items():
    for dst_label, dst_node in tlppo_graph.nodes.items():
        if dst_label in tlppo_graph.edges[src_label]:
            print(src_label, "-", dst_label, ": ", end="")
            print(tlppo_graph.edges[src_label][dst_label])

d = Display(w)
draw_graph(d, graph=graph)
draw_lppo(d, graph=graph, lppo=lppo)
plt.show()


def draw_tree(d: Display, tree: Tree):
    min_line_width = 0.001
    max_line_width = 0.003
    min_cost = .03  # min([min(costs.values()) for label, costs in graph.costs.items() if costs])
    max_cost = .8  # max([max(costs.values()) for label, costs in graph.costs.items() if costs])
    def line_width(cost):
        r = (cost - min_cost) / (max_cost - min_cost)
        return min_line_width + r * max_line_width

    def draw_node(d: Display, node: TreeNode, alpha: float):
        location = Location(node.state.values[0], node.state.values[1])
        d.circle(location, radius=.03, color="blue", alpha=alpha)
        for child in node.children:
            child_location = Location(child.state.values[0], child.state.values[1])
            reward = child.ucb1(c=0)
            width = line_width(reward)
            plt.text(child_location.x, child_location.y, "%f.2" % reward)
            d.arrow(location, child_location, color="orange", head_width=width * 2, line_width=width, alpha=reward)
            draw_node(d, child, alpha=alpha * .5)

    draw_node(d=d, node=tree.root, alpha=1.0)


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
