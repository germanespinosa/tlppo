import cellworld
def to_tuple(location: cellworld.Location) -> tuple:
    return round(location.x, 3), round(location.y, 3)


def to_location(value: tuple) -> cellworld.Location:
    return cellworld.Location(value[0], value[1])
