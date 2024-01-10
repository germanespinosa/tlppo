import typing
import cellworld
from tlppo import *


def to_tuple(location: cellworld.Location) -> tuple:
    return round(location.x, 3), round(location.y, 3)


def to_location(value: tuple) -> cellworld.Location:
    return cellworld.Location(value[0], value[1])


class CellworldLineOfSide(LineOfSight):
    def __init__(self, world: cellworld.World):
        self.visibility = cellworld.Location_visibility.from_world(world=world)

    def is_visible(self,
                   src: typing.Union[State, typing.Tuple[float, ...]],
                   dst: typing.Union[State, typing.Tuple[float, ...]]) -> bool:
        return self.visibility.is_visible(src=to_location(src), dst=to_location(dst))


class CellworldParticleSource(ParticleSource):
    def __init__(self, world: cellworld.World):
        self.cell_centers: typing.List[typing.Tuple[float, ...]] = [(cell.location.x, cell.location.y) for cell in world.cells if not cell.occluded]

    def get_particle(self) -> Particle:
        return Particle(state=State(values=random.choice(self.cell_centers)))


class CellworldStatePathFinder(StatePathFinder):

    def __init__(self, processed_paths: typing.Dict[int, typing.Dict[tuple, typing.List[tuple]]]):
        self.processed_paths: typing.Dict[int, typing.Dict[tuple, typing.List[tuple]]] = processed_paths

    @staticmethod
    def hash_value(value: float, precision=3) -> int:
        adv = 10 ** precision
        return int(value * adv)

    @staticmethod
    def hash_values(values: typing.Tuple[float, ...], precision=3) -> int:
        hash = 0
        adv = 10 ** precision
        mult = 1
        for value in values:
            hash += int(round(value, 3) * adv) * mult
            mult = mult * adv
        return hash

    @staticmethod
    def generate_paths(world: cellworld.World, paths: cellworld.Paths) -> typing.Dict[int, typing.Dict[int, typing.List[tuple]]]:
        visibility = cellworld.Location_visibility.from_world(world)
        processed_paths = dict()
        for src_cell in world.cells:
            print (src_cell.id)
            if src_cell.occluded:
                continue
            src_tuple = CellworldStatePathFinder.hash_values(to_tuple(src_cell.location))
            processed_paths[src_tuple] = dict()
            for dst_cell in world.cells:
                if dst_cell.occluded or src_cell == dst_cell:
                    continue
                path = paths.get_path(src_cell, dst_cell)
                processed_path = list()
                step = src_cell
                last_step_cell = step
                for step_cell in path:
                    if not visibility.is_visible(step.location, step_cell.location):
                        processed_path.append((last_step_cell.location.x, last_step_cell.location.y))
                        step = last_step_cell
                    last_step_cell = step_cell
                dst_tuple = CellworldStatePathFinder.hash_values((dst_cell.location.x, dst_cell.location.y))
                processed_path.append((dst_cell.location.x, dst_cell.location.y))
                processed_paths[src_tuple][dst_tuple] = processed_path
        return processed_paths

    def get_path(self,
                 src: typing.Union[State, typing.Tuple[float, ...]],
                 dst: typing.Union[State, typing.Tuple[float, ...]]) -> typing.List[typing.Tuple[float, ...]]:
        src_tuple = CellworldStatePathFinder.hash_values(src)
        dst_tuple = CellworldStatePathFinder.hash_values(dst)
        print(src_tuple, dst_tuple)
        return self.processed_paths[src_tuple][dst_tuple]

