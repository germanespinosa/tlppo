import typing
import cellworld
import tlppo
from .util import to_tuple, to_location


class LineOfSight(object):

    def __init__(self, world: cellworld.World):
        self.visibility = cellworld.Location_visibility.from_world(world=world)

    def is_valid(self, values: typing.Tuple[float, ...]) -> bool:
        occlusion: cellworld.Polygon
        for occlusion in self.visibility.occlusions:
            if occlusion.contains(cellworld.Location(values[0], values[1])):
                return False
        return True

    def __call__(self,
                 src: typing.Tuple[float, ...],
                 dst: typing.Tuple[float, ...]) -> bool:
        return self.visibility.is_visible(src=to_location(src), dst=to_location(dst))