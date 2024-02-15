import typing
import glob
import h5py
import pandas as pd
import tlppo
import csv
import json
import cellworld
import hexaworld


class Loader(object):
    @staticmethod
    def read_h5(file_path):
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

    @staticmethod
    def read_csv(file_path):
        with open(file_path, newline='') as csvfile:
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

    @staticmethod
    def load_files(file_pattern: str) -> tuple :
        sources: typing.List[typing.Tuple[float, ...]] = list()
        destinations: typing.List[typing.Tuple[float, ...]] = list()

        if "csv" in file_pattern:
            for file_path in glob.glob(file_pattern):
                columns, replay = Loader.read_csv(file_path)
                for row in replay:
                    sources.append(tuple(row['state'][:2]))
                    destinations.append(tuple(row['next_state'][:2]))
        elif "h5" in file_pattern:
            for file_path in glob.glob(file_pattern):
                replay = Loader.read_h5(file_path)
                for index, row in replay.iterrows():
                    sources.append(tuple(row['state'][:2]))
                    destinations.append(tuple(row['next_state'][:2]))
        else:
            raise ValueError("file_pattern must be csv or h5")

        return sources, destinations

    @staticmethod
    def create_graph(sources: typing.List[typing.Tuple[float, ...]],
                     destinations: typing.List[typing.Tuple[float, ...]],
                     state_count: int,
                     line_of_sight: hexaworld.LineOfSight) -> tlppo.Graph:
        clusters = tlppo.Clusters(data_points=sources + destinations, cluster_count=state_count)

        source_labels = clusters.get_labels(sources)
        destination_labels = clusters.get_labels(destinations)

        graph = tlppo.Graph()
        for values in clusters.centroids:
            graph.add_node(state=tlppo.State(values=(values[0], values[1])))

        for source_label, destination_label in zip(source_labels, destination_labels):
            if source_label == destination_label:
                continue
            if line_of_sight(src=clusters.centroids[source_label], dst=clusters.centroids[destination_label]):
                graph.connect(src_label=source_label, dst_label=destination_label)
        return graph

    @staticmethod
    def create_lppo_graph(graph: tlppo.Graph,
                          lppo_count: int,
                          depth: int) -> tlppo.Graph:
        lppos = graph.get_lppo(n=lppo_count, depth=depth)
        tlppo_graph = graph.get_subgraph(nodes=lppos)
        goal = tlppo_graph.add_node(state=tlppo.State(values=(1, .5)))
        for lppo in lppos:
            tlppo_graph.connect(lppo, goal.label)
        return tlppo_graph, lppos

    @staticmethod
    def create_belief_state(paths: cellworld.Paths,
                            line_of_sight: hexaworld.LineOfSight) -> hexaworld.CellworldBeliefState:
        path_finder = hexaworld.PathFinder(paths=paths, line_of_sight=line_of_sight)
        return hexaworld.CellworldBeliefState(world=paths.world, path_finder=path_finder, size=100, attempts=200)

    @staticmethod
    def create_tree(graph: tlppo.Graph,
                    values: typing.Tuple[float, ...],
                    line_of_sight: hexaworld.LineOfSight) -> tlppo.Tree:
        tree = tlppo.Tree(graph=graph, values=values)
        for label, node in graph.nodes.items():
            if not graph.edges[label]:
                continue
            if line_of_sight(values, node.state.values):
                tree.root.children.append(tlppo.TreeNode(graph=graph,
                                                         label=node.label,
                                                         state=node.state,
                                                         parent=tree.root))
        return tree

    @staticmethod
    def create_spatial_graph(world: cellworld.World):
        graph = tlppo.Graph()
        for cell in world.cells:
            graph.add_node(state=tlppo.State(values=hexaworld.to_tuple(cell.location)), label=cell.id)
        cell_graph = cellworld.Graph.create_connection_graph(world=world)
        for cell in world.cells:
            for conn in cell_graph[cell]:
                graph.connect(cell.id, conn)
        return graph

    arrows = []
    @staticmethod
    def clear_tree(display: cellworld.Display):
        for arrow in Loader.arrows:
            display.arrow(beginning=cellworld.Location(0, 0),
                          ending=cellworld.Location(0, 0),
                          existing_arrow=arrow,
                          alpha=0)


    @staticmethod
    def plot_tree(tree: tlppo.Tree, display: cellworld.Display):
        def plot_node(node: tlppo.TreeNode, alpha: float):
            node_location = hexaworld.to_location(node.state.values)
            #display.circle(location=node_location, radius=.01, color="purple")
            if node.children:
                max_visits = max([child.visits for child in node.children])
            else:
                max_visits = 0
            for child in node.children:
                if child.visits == 0:
                    continue
                child_location = hexaworld.to_location(child.state.values)
                child_alpha = alpha * child.visits / max_visits
                if plot_node.arrow_count < len(Loader.arrows):
                    existing_arrow = Loader.arrows[plot_node.arrow_count]
                    display.arrow(beginning=node_location,
                                  ending=child_location,
                                  color="purple",
                                  alpha=child_alpha,
                                  existing_arrow=existing_arrow,
                                  zorder=-0)
                    plot_node.arrow_count += 1
                else:
                    new_arrow = display.arrow(beginning=node_location,
                                              ending=child_location,
                                              color="purple",
                                              alpha=child_alpha,
                                              zorder=-0)

                    Loader.arrows.append(new_arrow)
                #plot_node(node=child, alpha=child_alpha)
        plot_node.arrow_count = 0
        plot_node(node=tree.root, alpha=1.0)
