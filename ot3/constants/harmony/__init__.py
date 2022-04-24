"""Definition of family_data_per_family and rest_duration"""

from . import definitions
from . import envelopes
from . import nature


import typing

from mutwo import generators
from mutwo import utilities

from ot3.constants import duration as ot3_duration
from ot3.utilities import tools


WindDataPerFamily = typing.Tuple[typing.Tuple[float, float, int], ...]
DurationPerRest = typing.Tuple[float, ...]


def _calculate_wind_data(
    composition_duration_in_seconds: float,
) -> typing.Tuple[WindDataPerFamily, DurationPerRest]:
    wind_data = []
    duration_per_rest = []
    family_duration = 0
    while family_duration < composition_duration_in_seconds:
        absolute_position = family_duration / composition_duration_in_seconds

        duration_percentage = envelopes.DURATION.value_at(absolute_position)
        speed_percentage = envelopes.SPEED.value_at(absolute_position)
        strength_percentage = envelopes.STRENGTH.value_at(absolute_position)
        rest_duration_percentage = envelopes.REST_DURATION.value_at(absolute_position)

        duration = utilities.tools.scale(
            duration_percentage,
            0,
            1,
            definitions.MIN_DURATION_FOR_FAMILY,
            definitions.MAX_DURATION_FOR_FAMILY,
        )
        duration_of_root = utilities.tools.scale(
            speed_percentage,
            0,
            1,
            definitions.MIN_DURATION_FOR_ROOT,
            definitions.MAX_DURATION_FOR_ROOT,
        )
        strength = utilities.tools.scale(
            strength_percentage,
            0,
            1,
            definitions.MIN_MOVEMENT_SPAN,
            definitions.MAX_MOVEMENT_SPAN,
        )
        rest_duration = utilities.tools.scale(
            rest_duration_percentage,
            0,
            1,
            definitions.MIN_DURATION_FOR_REST,
            definitions.MAX_DURATION_FOR_REST,
        )

        wind_data.append((duration, duration_of_root, strength))
        duration_per_rest.append(rest_duration)

        family_duration += duration + rest_duration

    return tuple(wind_data), tuple(duration_per_rest[:-1])


FamilyDataPerFamily = typing.Tuple[
    typing.Tuple[nature.RootPitches, nature.ConnectionPitches, nature.Duration], ...
]


def _calculate_family_data_per_family(
    wind_data_per_family: WindDataPerFamily,
) -> FamilyDataPerFamily:
    n_families = len(wind_data_per_family)

    pendulum_per_family = tools.not_fibonacci_transition(
        *generators.toussaint.euclidean(n_families, 2),
        nature.PENDULUM0,
        nature.PENDULUM1
    )

    activity_level = generators.edwards.ActivityLevel()

    family_data_per_family = []
    for wind_data, pendulum in zip(wind_data_per_family, pendulum_per_family):
        direction = bool(activity_level(5))
        wind = nature.Wind(*wind_data, direction)
        family_data = wind.move(pendulum)
        family_data_per_family.append(family_data)

    return family_data_per_family


_wind_data_per_family, DURATION_PER_REST = _calculate_wind_data(
    ot3_duration.DURATION_IN_SECONDS
)
FAMILY_DATA_PER_FAMILY = _calculate_family_data_per_family(_wind_data_per_family)
