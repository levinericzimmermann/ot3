"""Definition of global 'FamilyOfPitchCurves'.
"""

import typing

from mutwo.converters.frontends import ekmelily_constants
from mutwo.events import basic
from mutwo.events import families
from mutwo import utilities

from ot3 import constants as ot3_constants


def _concatenate_families(
    families_pitch: basic.SequentialEvent[
        typing.Union[basic.SimpleEvent, families.FamilyOfPitchCurves]
    ]
) -> families.FamilyOfPitchCurves:
    absolute_entry_delay_and_family_of_pitch_curve_pairs = [
        (absolute_entry_delay, family_of_pitch_curves)
        for absolute_entry_delay, family_of_pitch_curves in zip(
            families_pitch.absolute_times, families_pitch
        )
        if type(family_of_pitch_curves) != basic.SimpleEvent
    ]
    return families.FamilyOfPitchCurves.from_families_of_curves(
        *absolute_entry_delay_and_family_of_pitch_curve_pairs
    )


def _filter_curves_with_unnotateable_pitches(
    family_of_pitch_curves: families.FamilyOfPitchCurves,
) -> families.FamilyOfPitchCurves:
    def condition(pitch_curve: families.PitchCurve) -> bool:
        pitch = pitch_curve.pitch
        is_notateable = True
        for exponent, prime in zip(pitch.exponents, pitch.primes):
            if prime > 3:
                try:
                    max_exponent = ekmelily_constants.DEFAULT_PRIME_TO_HIGHEST_ALLOWED_EXPONENT[
                        prime
                    ]
                except KeyError:
                    max_exponent = None
                    is_notateable = False
                if max_exponent and abs(exponent) > max_exponent:
                    is_notateable = False
        return is_notateable

    return family_of_pitch_curves.filter(condition, mutate=False)


@utilities.decorators.compute_lazy(
    "ot3/constants/FAMILIES_PITCH.pickle",
    force_to_compute=ot3_constants.compute.COMPUTE_FAMILIES_PITCH,
)
def _make_families() -> basic.SequentialEvent[
    typing.Union[basic.SimpleEvent, families.FamilyOfPitchCurves]
]:
    families_pitch = basic.SequentialEvent(
        [basic.SimpleEvent(REST_DURATION_BEFORE_FIRST_FAMILY_ARRIVES)]
    )
    for family_data, duration_per_rest in zip(
        ot3_constants.harmony.FAMILY_DATA_PER_FAMILY,
        ot3_constants.harmony.DURATION_PER_REST + (None,),
    ):
        root_pitches, connection_pitches, duration = family_data
        family = families.RootAndConnectionBasedFamilyOfPitchCurves(
            duration,
            root_pitches,
            connection_pitches,
            allowed_primes=(2, 3, 5, 7),
            generations=GENERATIONS,
            population_size=POPULATION_SIZE,
            root_register_to_weight={
                -3: 0.1,
                -2: 0.2,
                -1: 0.75,
                0: 1,
                1: 0.75,
                2: 0.2,
                3: 0.1,
            },
        )
        families_pitch.append(family)
        if duration_per_rest:
            rest = basic.SimpleEvent(duration_per_rest)
            families_pitch.append(rest)

    return families_pitch


GENERATIONS = 600
# GENERATIONS = 100
POPULATION_SIZE = 120
# POPULATION_SIZE = 80

REST_DURATION_BEFORE_FIRST_FAMILY_ARRIVES = 30
FAMILIES_PITCH = _make_families()

# omit family 15 for making serenade at this position
FAMILIES_PITCH[15] = basic.SimpleEvent(FAMILIES_PITCH[15].duration)

FAMILY_PITCH = _concatenate_families(FAMILIES_PITCH)
FAMILY_PITCH_ONLY_WITH_NOTATEABLE_PITCHES = _filter_curves_with_unnotateable_pitches(
    FAMILY_PITCH
)
# FAMILY_PITCH.show_plot()  # insane plot showing function


NOTATEABLE_PITCH_TO_PITCH_COUNTER = {}
for curve in FAMILY_PITCH_ONLY_WITH_NOTATEABLE_PITCHES:
    pitch_as_exponents = curve.pitch.exponents
    if pitch_as_exponents in NOTATEABLE_PITCH_TO_PITCH_COUNTER:
        NOTATEABLE_PITCH_TO_PITCH_COUNTER[pitch_as_exponents] += 1
    else:
        NOTATEABLE_PITCH_TO_PITCH_COUNTER.update({pitch_as_exponents: 1})
