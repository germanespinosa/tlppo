import typing

import matplotlib.pyplot as plt


def get_color_map(values:typing.List[float], color_map = plt.cm.Reds):
    min_v, max_v = min(values), max(values)
    adjusted_values = [(v - min_v) / (max_v - min_v) for v in values]
    return color_map(adjusted_values)
