import typing

import numpy as np

from mutwo import events
from mutwo import parameters
from mutwo import utilities

from ot3 import constants as ot3_constants
from ot3 import converters as ot3_converters

from ot3.converters.symmetrical.time_brackets import StartTimeToTimeBracketsConverter


class FamiliesPitchToSaturationTonesConverter(StartTimeToTimeBracketsConverter):
    def __init__(
        self,
        family_of_pitch_curves: events.families.FamilyOfPitchCurves,
        seed: int = 20000000,
    ):
        super().__init__(family_of_pitch_curves, 0)
        self._random = np.random.default_rng(seed)
        self._picker = (
            ot3_converters.symmetrical.families.PickSaturationPitchFromCurveAndWeightPairsConverter()
        )

    def _make_saturation_tone(
        self,
        absolute_position: float,
        start_position: parameters.abc.DurationType,
        saturation_tone_span: parameters.abc.DurationType,
        end_point: parameters.abc.DurationType,
    ) -> events.time_brackets.TimeBracket:
        time_bracket_ratio = ot3_constants.saturations.TIME_BRACKET_RATIO.value_at(
            absolute_position
        )
        stable_area_duration = utilities.tools.scale(
            time_bracket_ratio, 0, 1, saturation_tone_span * 0.01, saturation_tone_span
        )
        uncertain_area_duration = saturation_tone_span - stable_area_duration
        uncertain_area_duration_for_each_position = uncertain_area_duration / 2
        current_voice = next(ot3_constants.saturations.VOICE_CYCLE)
        if current_voice.technique == "sine":
            voice_tag = ot3_constants.instruments.SINE_VOICE_AND_CHANNEL_TO_ID[
                (current_voice.nth_voice, current_voice.nth_channel)
            ]
        else:
            voice_tag = ot3_constants.instruments.MODE_VOICE_AND_CHANNEL_TO_ID[
                (current_voice.nth_voice, current_voice.nth_channel)
            ]
        start_range = (
            start_position,
            uncertain_area_duration_for_each_position + start_position,
        )
        end_range = (end_point - uncertain_area_duration_for_each_position, end_point)
        time_bracket = events.time_brackets.TimeBracket(
            [
                events.basic.TaggedSimultaneousEvent(
                    [events.basic.SequentialEvent([events.music.NoteLike([], 1)])],
                    tag=voice_tag,
                )
            ],
            start_or_start_range=start_range,
            end_or_end_range=end_range,
            seed=int(start_position),
        )
        time_bracket = self._assign_curve_and_weight_pairs_on_events.convert(
            time_bracket
        )
        time_bracket = self._picker.convert(time_bracket)
        return time_bracket

    def _populate_family(
        self,
        absolute_entry_delay: parameters.abc.DurationType,
        duration_of_families_pitch: parameters.abc.DurationType,
        family_of_pitch_curves: events.families.FamilyOfPitchCurves,
    ) -> typing.Tuple[events.time_brackets.TimeBracket, ...]:
        time_brackets = []
        duration_of_family = family_of_pitch_curves.duration
        start_point = absolute_entry_delay
        absolute_end_point = 0
        while (
            absolute_end_point
            < duration_of_family + absolute_entry_delay + ot3_constants.saturations.TAIL
        ):
            absolute_position = start_point / duration_of_families_pitch
            saturation_tone_span = ot3_constants.saturations.DURATION.value_at(
                absolute_position
            )
            absolute_end_point = start_point + saturation_tone_span
            time_brackets.append(
                self._make_saturation_tone(
                    absolute_position,
                    start_point,
                    saturation_tone_span,
                    absolute_end_point,
                )
            )

            density = ot3_constants.saturations.DENSITY.value_at(absolute_position)
            min_delay_until_next_point = saturation_tone_span / len(
                ot3_constants.saturations.VOICE_CYCLE_BLUEPRINT
            )
            delay_until_next_point = utilities.tools.scale(
                density, 0, 1, saturation_tone_span, min_delay_until_next_point
            )
            start_point += delay_until_next_point
        return tuple(time_brackets)

    def convert(
        self,
        families_pitch: events.basic.SequentialEvent[
            typing.Union[events.basic.SimpleEvent, events.families.FamilyOfPitchCurves]
        ],
    ) -> typing.Tuple[events.time_brackets.TimeBracket, ...]:
        duration = families_pitch.duration
        time_brackets = []
        for absolute_entry_delay, family_of_pitch_curves_or_simple_event in zip(
            families_pitch.absolute_times, families_pitch
        ):
            if isinstance(
                family_of_pitch_curves_or_simple_event,
                events.families.FamilyOfPitchCurves,
            ):
                absolute_position = absolute_entry_delay / duration
                populate_family_likelihood = ot3_constants.saturations.POPULATE_FAMILY_LIKELIHOOD.value_at(
                    absolute_position
                )
                if self._random.uniform(0, 1) < populate_family_likelihood:
                    time_brackets.extend(
                        self._populate_family(
                            absolute_entry_delay,
                            duration,
                            family_of_pitch_curves_or_simple_event,
                        )
                    )

        return tuple(time_brackets)
