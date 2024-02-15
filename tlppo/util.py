import typing
import random


def distance(src: typing.Tuple[float, ...],
             dst: typing.Tuple[float, ...]) -> float:
    return sum((p1 - p2) ** 2 for p1, p2 in zip(src, dst)) ** 0.5


def negative(x: typing.Tuple[float, ...]) -> typing.Tuple[float,...]:
    return tuple(-v for v in x)


def addition(src: typing.Tuple[float, ...],
             dst: typing.Tuple[float, ...]) -> typing.Tuple[float, ...]:
    return tuple(p1 + p2 for p1, p2 in zip(src, dst))


def subtraction(src: typing.Tuple[float, ...],
                dst: typing.Tuple[float, ...]) -> typing.Tuple[float, ...]:
    return tuple(p1 - p2 for p1, p2 in zip(src, dst))


def magnitude(values: typing.Tuple[float, ...]) -> float:
    return sum(p1 ** 2 for p1 in values) ** 0.5


def normalize(values: typing.Tuple[float, ...]) -> typing.Tuple[float, ...]:
    m = magnitude(values)
    return tuple(x / m for x in values)


def direction(src: typing.Tuple[float, ...],
              dst: typing.Tuple[float, ...]) -> typing.Tuple[float, ...]:
    diff = subtraction(dst, src)
    return normalize(diff)


def move(src: typing.Tuple[float,...],
         dst: typing.Tuple[float, ...],
         dist: float) -> typing.Tuple[float, ...]:
    d = direction(src, dst)
    return tuple(p1 + p2 * dist for p1, p2 in zip(src, d))


def noisy_copy(src: typing.Tuple[float, ...],
               noise: float) -> typing.Tuple[float, ...]:
    return move(src=src,
                dst=tuple(random.random() for _ in range(len(src))),
                dist=random.random() * noise)

