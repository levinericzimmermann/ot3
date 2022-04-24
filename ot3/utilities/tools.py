import functools
import itertools
import operator
import typing

from mutwo import generators
from mutwo import parameters


def make_brownian_rhythm(
    duration: parameters.abc.DurationType,
    average_note_duration: parameters.abc.DurationType,
    random_state: int = 10,
    dt: float = 2,
    delta: float = 1,
) -> typing.Tuple[parameters.abc.DurationType, ...]:
    n_items = int(duration // average_note_duration)
    rhythm = (duration - 1,)
    while sum(rhythm) < duration:
        rhythm = list(
            abs(
                generators.brown.random_walk_noise(
                    average_note_duration, n_items, dt, delta, random_state=random_state
                )
            )
        )
        n_items += 1

    while len(rhythm) > 1 and sum(rhythm) > duration:
        rhythm = rhythm[:-1]

    difference = duration - sum(rhythm)
    rhythm[-1] += difference
    while rhythm[-1] < 0:
        rhythm[-2] += rhythm[-1]
        rhythm = rhythm[:-1]

    assert round(sum(rhythm), 2) == round(duration, 2)

    return tuple(rhythm)


def make_growing_series_with_sum_n(requested_sum: int) -> tuple:
    ls = []
    add_idx = iter([])
    while sum(ls) < requested_sum:
        try:
            ls[next(add_idx)] += 1
        except StopIteration:
            ls = [1] + ls
            add_idx = reversed(tuple(range(len(ls))))
    return tuple(ls)


def make_falling_series_with_sum_n(requested_sum: int) -> tuple:
    return tuple(reversed(make_growing_series_with_sum_n(requested_sum)))


def interlock_tuples(t0: tuple, t1: tuple) -> tuple:
    size0, size1 = len(t0), len(t1)
    difference = size0 - size1
    indices = functools.reduce(
        operator.add, ((0, 1) for n in range(min((size0, size1))))
    )
    if difference > 0:
        indices = tuple(0 for i in range(difference)) + indices
    else:
        indices = indices + tuple(1 for i in range(abs(difference)))
    t0_it = iter(t0)
    t1_it = iter(t1)
    return tuple(next(t0_it) if idx == 0 else next(t1_it) for idx in indices)


def not_fibonacci_transition(size0: int, size1: int, element0=0, element1=1) -> tuple:
    def write_to_n_element(it, element) -> tuple:
        return tuple(tuple(element for n in range(x)) for x in it)

    if size0 == 0 and size1 == 0:
        return tuple([])

    elif size0 == 0:
        return tuple([element1 for n in range(size1)])

    elif size1 == 0:
        return tuple([element0 for n in range(size0)])

    else:
        return functools.reduce(
            operator.add,
            interlock_tuples(
                *tuple(
                    write_to_n_element(s, el)
                    for s, el in zip(
                        (
                            make_falling_series_with_sum_n(size0),
                            make_growing_series_with_sum_n(size1),
                        ),
                        (element0, element1),
                    )
                )
            ),
        )


def make_gray_code_rhythm_cycle(n=3):
    gray_codes = tuple(
        tuple([1, 2][number] for number in gray_code)
        for gray_code in generators.gray.reflected_binary_code(n, 2)
    )
    return itertools.cycle(gray_codes)
