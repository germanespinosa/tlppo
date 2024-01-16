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

    def process_path(self,
                     path: typing.List[typing.Tuple[float, float]]) -> typing.List[typing.Tuple[float, float]]:
        last_step = path[0]
        processed_path = [last_step]
        for step in path:
            if not self.line_of_sight(processed_path[-1], step):
                processed_path.append(last_step)
            last_step = step
        processed_path.append(path[-1])
        return processed_path

    def get_path(self,
                 src: typing.Union[tlppo.State, typing.Tuple[float, ...]],
                 dst: typing.Union[tlppo.State, typing.Tuple[float, ...]]) -> typing.List[typing.Tuple[float, ...]]:
        if isinstance(src, tlppo.State):
            src = src.values
        if isinstance(dst, tlppo.State):
            dst = dst.values

        src_cell_index = self.paths.world.cells.find(to_location(src))
        dst_cell_index = self.paths.world.cells.find(to_location(dst))

        path = self.paths.get_path(src_cell=self.paths.world.cells[src_cell_index],
                                   dst_cell=self.paths.world.cells[dst_cell_index])

        processed_path = [src] + [to_tuple(self.paths.world.cells[c.id].location) for c in path] + [dst]
        return self.process_path(processed_path)
