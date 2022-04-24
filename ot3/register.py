"""Script for building and registering time brackets at the global TimeBracketContainer

Public interaction via "main" method.
"""

from mutwo import events
from mutwo import utilities

from ot3 import constants as ot3_constants
from ot3 import converters as ot3_converters
from ot3 import stochastic  # no module in mutwo with same name


def _register_serenades():
    for serenade in ot3_constants.serenades.SERENADES.values():
        ot3_constants.time_brackets_container.TIME_BRACKETS.register(serenade)


def _register_westminster():
    converter = ot3_converters.symmetrical.westminster.WestminsterMelodiesToTimeBracketsConverter(
        ot3_constants.families_pitch.FAMILIES_PITCH
    )
    time_brackets_to_register = converter.convert(
        ot3_constants.westminster.ADAPTED_WESTMINSTER_MELODIES
    )
    n_overlaps_between_westminster_melodies = 0
    for time_bracket in time_brackets_to_register:
        try:
            ot3_constants.time_brackets_container.TIME_BRACKETS.register(time_bracket)
        except Exception:
            n_overlaps_between_westminster_melodies += 1

    print(
        f"Found {n_overlaps_between_westminster_melodies} overlaps between Westminster"
        " melodies"
    )


def _register_modes():
    converter = ot3_converters.symmetrical.modes.FamiliesPitchToModesConverter(
        seed=13123123555
    )
    time_brackets = converter.convert(ot3_constants.families_pitch.FAMILIES_PITCH)
    for time_bracket in time_brackets:
        ot3_constants.time_brackets_container.TIME_BRACKETS.register(
            time_bracket, tags_to_analyse=(time_bracket[0].tag,)
        )


def _register_saturations():
    @utilities.decorators.compute_lazy(
        "ot3/constants/.saturation_tones.pickle",
        force_to_compute=ot3_constants.compute.COMPUTE_SATURATION_TONES,
    )
    def compute_saturation_time_brackets():
        converter = ot3_converters.symmetrical.saturations.FamiliesPitchToSaturationTonesConverter(
            ot3_constants.families_pitch.FAMILY_PITCH
        )
        return converter.convert(ot3_constants.families_pitch.FAMILIES_PITCH)

    saturation_time_brackets = compute_saturation_time_brackets()
    for time_bracket in saturation_time_brackets:
        ot3_constants.time_brackets_container.TIME_BRACKETS.register(
            time_bracket, tags_to_analyse=(time_bracket[0].tag,)
        )


def _register_stochastic_brackets():
    collected_time_brackets = stochastic.main()
    for instrument_id, time_bracket in collected_time_brackets:
        try:
            ot3_constants.time_brackets_container.TIME_BRACKETS.register(
                time_bracket, tags_to_analyse=(instrument_id,)
            )
        except utilities.exceptions.OverlappingTimeBracketsError:
            pass


def _remove_superfluous_time_brackets():
    border = (42 * 60) + 20
    new_time_bracket_container = []
    for time_bracket in ot3_constants.time_brackets_container.TIME_BRACKETS:
        if time_bracket.minimal_start < border:
            new_time_bracket_container.append(time_bracket)

    ot3_constants.time_brackets_container.TIME_BRACKETS = events.time_brackets.TimeBracketContainer(
        new_time_bracket_container
    )


def main():
    _register_serenades()
    _register_modes()
    _register_saturations()
    _register_westminster()
    _register_stochastic_brackets()
    _remove_superfluous_time_brackets()
