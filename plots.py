from cellworld import *
from tlppo import *


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
                display.arrow(src_location, dst_location, color="orange", head_width=width * 2, line_width=width)
                src_location = dst_location
                src_node = dst_node
            cost = graph.costs[label][connection_label]
            width = line_width(cost)
            display.arrow(node_location, dst_location, color="blue", head_width=width * 2, line_width=width, alpha=.5)


def draw_lppo(display: Display, graph: Graph, lppo: typing.List[int]):
    for label in lppo:
        node = graph.nodes[label]
        node_location = Location(node.state.values[0], node.state.values[1])
        display.circle(node_location, color="green", radius=.02)


def draw_tree(display: Display, tree: Tree):
    min_line_width = 0.001
    max_line_width = 0.003
    min_cost = .03  # min([min(costs.values()) for label, costs in graph.costs.items() if costs])
    max_cost = .8  # max([max(costs.values()) for label, costs in graph.costs.items() if costs])

    def line_width(cost):
        r = (cost - min_cost) / (max_cost - min_cost)
        return min_line_width + r * max_line_width

    def draw_node(display: Display, node: TreeNode, alpha: float):
        location = Location(node.state.values[0], node.state.values[1])
        display.circle(location, radius=.03, color="blue", alpha=alpha)
        for child in node.children:
            child_location = Location(child.state.values[0], child.state.values[1])
            reward = child.ucb1(c=0)
            width = line_width(reward)
            plt.text(child_location.x, child_location.y, "%f.2" % reward)
            display.arrow(location, child_location, color="orange", head_width=width * 2, line_width=width, alpha=reward)
            draw_node(display, child, alpha=alpha * .5)

    draw_node(display=display, node=tree.root, alpha=1.0)

