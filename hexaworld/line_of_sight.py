import typing
import cellworld
import tlppo
from .util import to_tuple, to_location


class LineOfSight(object):

    def __init__(self, world: cellworld.World):
        self.visibility = cellworld.Location_visibility.from_world(world=world)

    def __call__(self,
                 src: typing.Union[tlppo.State, typing.Tuple[float, ...]],
                 dst: typing.Union[tlppo.State, typing.Tuple[float, ...]]) -> bool:
        if isinstance(src, tlppo.State):
            src = src.values
        if isinstance(dst, tlppo.State):
            dst = dst.values
        return self.visibility.is_visible(src=to_location(src), dst=to_location(dst))