import random
import typing
import cellworld
import tlppo
from .util import to_location, to_tuple
from .line_of_sight import LineOfSight


class PathFinder(object):

    def __init__(self,
                 paths: cellworld.Paths,
                 line_of_sight: LineOfSight):
        self.paths = paths
        self.line_of_sight = line_of_sight
        self.free_cells = self.paths.world.cells.free_cells()

    def process_path(self,
                     path: typing.List[typing.Tuple[float, ...]]) -> typing.List[typing.Tuple[float, ...]]:
        last_step = path[0]
        processed_path = [last_step]
        for step in path:
            if not self.line_of_sight(processed_path[-1], step):
                processed_path.append(last_step)
            last_step = step
        processed_path.append(path[-1])
        return processed_path

    def get_path(self,
                 src: typing.Tuple[float, ...],
                 dst: typing.Tuple[float, ...]) -> typing.List[typing.Tuple[float, ...]]:

        src_cell_index = self.free_cells.find(to_location(src))
        dst_cell_index = self.free_cells.find(to_location(dst))

        path = self.paths.get_path(src_cell=self.free_cells[src_cell_index],
                                   dst_cell=self.free_cells[dst_cell_index])

        processed_path = [src] + [to_tuple(self.paths.world.cells[c.id].location) for c in path] + [dst]
        return self.process_path(processed_path)

    def get_random_path(self,
                        src: typing.Tuple[float, ...]):
        src_cell_index = self.free_cells.find(to_location(src))
        dst_cell = random.choice(self.free_cells)
        path = self.paths.get_path(src_cell=self.free_cells[src_cell_index],
                                   dst_cell=dst_cell)

        processed_path = [src] + [to_tuple(self.paths.world.cells[c.id].location) for c in path] + [to_tuple(dst_cell.location)]
        return self.process_path(processed_path)
