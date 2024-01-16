import pickle
import typing
import glob
import h5py
import pandas as pd
import tlppo
import csv
import json
import cellworld
import os
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
        lppo = graph.get_lppo(n=lppo_count, depth=depth)
        tlppo_graph = graph.get_subgraph(nodes=lppo)
        return tlppo_graph, lppo

    @staticmethod
    def create_particle_filter(paths: cellworld.Paths,
                               line_of_sight: hexaworld.LineOfSight) -> hexaworld.CellworldParticleFilter:
        path_finder = hexaworld.PathFinder(paths=paths, line_of_sight=line_of_sight)
        return hexaworld.CellworldParticleFilter(world=paths.world, path_finder=path_finder)

    @staticmethod
    def create_tree(graph: tlppo.Graph,
                    values: typing.Tuple[float, ...],
                    line_of_sight: hexaworld.LineOfSight) -> tlppo.Tree:
        tree = tlppo.Tree(graph=graph, values=values)
        for label, node in graph.nodes.items():
            if not graph.edges[label]:
                continue
            if line_of_sight(values, node.state):
                tree.root.children.append(tlppo.TreeNode(graph=graph,
                                                         label=node.label,
                                                         state=node.state,
                                                         parent=tree.root))
        return tree
