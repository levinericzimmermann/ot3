"""Module for converting global `FamilyOfPitchCurves` varibale to TimeBracket"""

import abc
import itertools
import operator
import typing

import expenvelope

from mutwo import converters
from mutwo import events
from mutwo import generators
from mutwo import parameters

from ot3 import constants as ot3_constants
from ot3 import converters as ot3_converters
from ot3 import events as ot3_events
from ot3 import parameters as ot3_parameters
from ot3 import utilities as ot3_utilities

DEFAULT_MINIMAL_OVERLAPPING_PERCENTAGE = 0.75


def _add_copy_for_flageoletts_playing_suggestion(
    time_bracket: events.time_brackets.TimeBracket,
):
    def remove_harmonics(
        playing_indicators: ot3_parameters.playing_indicators.OT2PlayingIndicatorCollection,
    ):
        playing_indicators.precise_double_harmonic.string_pitch0 = None
        playing_indicators.precise_double_harmonic.string_pitch1 = None
        playing_indicators.precise_double_harmonic.played_pitch0 = None
        playing_indicators.precise_double_harmonic.played_pitch1 = None
        playing_indicators.precise_natural_harmonic.played_pitch = None
        playing_indicators.precise_natural_harmonic.string_pitch = None

    sounding_pitches = time_bracket[0][0]
    playing_suggestion = sounding_pitches.copy()
    # playing_suggestion.tag = ot3_constants.instruments.ID_VIOLIN_FLAGEOLLETES
    sounding_pitches.mutate_parameter("playing_indicators", remove_harmonics)
    time_bracket[0].append(playing_suggestion)


class StartTimeToTimeBracketsConverter(converters.abc.Converter):
    def __init__(
        self,
        family_of_pitch_curves: events.families.FamilyOfPitchCurves,
        minimal_overlapping_percentage: float = DEFAULT_MINIMAL_OVERLAPPING_PERCENTAGE,
    ):
        self._family_of_pitch_curves = family_of_pitch_curves
        self._minimal_overlapping_percentage = minimal_overlapping_percentage
        if family_of_pitch_curves:
            self._assign_curve_and_weight_pairs_on_events = converters.symmetrical.families.AssignCurveAndWeightPairsOnEventsConverter(
                self._family_of_pitch_curves
            )

    @staticmethod
    def _quantize_time(
        time: parameters.abc.DurationType,
        quantization_step: parameters.abc.DurationType = 5,
    ) -> parameters.abc.DurationType:
        return round(time / quantization_step) * quantization_step

    @staticmethod
    def _is_sequential_event_empty(
        sequential_event_to_analyse: events.basic.SequentialEvent[
            events.basic.SimpleEvent
        ],
    ) -> bool:
        for simple_event in sequential_event_to_analyse:
            if (
                hasattr(simple_event, "pitch_or_pitches")
                and len(simple_event.pitch_or_pitches) > 0
            ):
                return False

        return True

    def _filter_family_by_minimal_overlapping_percentage(
        self,
        time_ranges: typing.Tuple[
            events.time_brackets.TimeRange, events.time_brackets.TimeRange
        ],
    ) -> float:
        time_range = (time_ranges[0][0], time_ranges[1][1])

        def condition(pitch_curve: events.families.PitchCurve) -> bool:
            overlapping_percentage = pitch_curve.get_overlapping_percentage_with_active_ranges(
                time_range
            )
            return overlapping_percentage >= self._minimal_overlapping_percentage

        return self._family_of_pitch_curves.filter(condition, mutate=False)

    def _are_curves_available_within_minimal_overlapping_percentage(
        self,
        time_ranges: typing.Tuple[
            events.time_brackets.TimeRange, events.time_brackets.TimeRange
        ],
    ) -> bool:
        return (
            len(self._filter_family_by_minimal_overlapping_percentage(time_ranges)) > 0
        )

    @abc.abstractmethod
    def convert(
        self, start_time: parameters.abc.DurationType,
    ) -> typing.Tuple[events.time_brackets.TimeBracket, ...]:
        raise NotImplementedError


class StartTimeToInstrumentTimeBracketsConverter(StartTimeToTimeBracketsConverter):
    def __init__(
        self,
        family_of_pitch_curves,
        minimal_overlapping_percentage=DEFAULT_MINIMAL_OVERLAPPING_PERCENTAGE,
        seed=3233,
    ):
        super().__init__(
            family_of_pitch_curves,
            minimal_overlapping_percentage=minimal_overlapping_percentage,
        )

        import random as tbc_random

        tbc_random.seed(seed)
        self._random = tbc_random

    def _add_drone_to_notation(
        self, time_bracket: events.time_brackets.TimeBracket,
    ):
        time_range = (time_bracket.minimal_start, time_bracket.maximum_end)

        def cut_out_unused_events(pitch_curve: events.families.PitchCurve) -> bool:
            return (
                pitch_curve.tag == "root"
                and pitch_curve.get_overlapping_percentage_with_active_ranges(
                    time_range
                )
                > 0.1
            )

        filtered_family = self._family_of_pitch_curves.filter(
            cut_out_unused_events, mutate=False
        )
        filtered_family.cut_out(*time_range, mutate=False)
        filtered_family.filter_curves_with_tag("root")
        if filtered_family:
            most_important_root = max(
                filtered_family, key=lambda curve: curve.weight_curve.average_level()
            )
            root_pitch, _ = max(
                most_important_root.registered_pitch_and_weight_pairs,
                key=operator.itemgetter(1),
            )
            root_pitch.register(0)
            sequential_event_to_add = events.basic.SequentialEvent(
                [events.music.NoteLike(root_pitch, time_bracket[0][0].duration, "p")]
            )
            tagged_simultaneous_event = events.basic.TaggedSimultaneousEvent(
                [sequential_event_to_add], tag=ot3_constants.instruments.ID_DRONE
            )
            time_bracket.append(tagged_simultaneous_event)

    def _add_cent_deviation(
        self,
        sequential_event_to_process: events.basic.SequentialEvent[
            events.music.NoteLike
        ],
    ):
        for event in sequential_event_to_process:
            if (
                hasattr(event, "pitch_or_pitches")
                and event.pitch_or_pitches
                # don't write cent deviation for harmonics
                and not event.playing_indicators.precise_natural_harmonic.played_pitch
                and not event.playing_indicators.precise_double_harmonic.played_pitch0
                # and don't write cent deviation for multiphonics
                and not len(event.pitch_or_pitches) > 1
            ):
                pitch_to_process = event.pitch_or_pitches[0]
                deviation = (
                    pitch_to_process.cent_deviation_from_closest_western_pitch_class
                )
                event.notation_indicators.cent_deviation.deviation = deviation

    def _make_copy_of_content_for_sine_tone(
        self,
        start_time: parameters.abc.DurationType,
        converted_time_bracket: events.time_brackets.TimeBracket,
        for_repetition: bool = False,
    ):
        absolute_position = (
            start_time / ot3_constants.families_pitch.FAMILIES_PITCH.duration
        )
        if for_repetition:
            tag_to_search = self._instrument_id + "repetition"
        else:
            tag_to_search = self._instrument_id
        sine_tags = ot3_constants.instruments.ID_INSTR_TO_ID_SINES[tag_to_search]

        sine_tone_brackets = []
        for sine_tag in sine_tags:
            likelihood_envelope = ot3_constants.sines.ID_SINE_TO_LIKELIHOOD[sine_tag]
            if self._random.random() < likelihood_envelope.value_at(absolute_position):
                sine_tone_event = events.basic.TaggedSimultaneousEvent(
                    [converted_time_bracket[0][0].copy()], tag=sine_tag,
                )
                tb = events.time_brackets.TimeBracket(
                    [sine_tone_event],
                    converted_time_bracket.start_or_start_range,
                    converted_time_bracket.end_or_end_range,
                    seed=int(id(sine_tag) + (start_time * 4)),
                )
                sine_tone_brackets.append(tb)
        return sine_tone_brackets


class StartTimeToCalligraphicLineConverter(StartTimeToInstrumentTimeBracketsConverter):
    def __init__(
        self,
        instrument_id: str,
        family_of_pitch_curves: events.families.FamilyOfPitchCurves,
        instrument_ambitus: ot3_parameters.ambitus.Ambitus,
        minimal_overlapping_percentage: float = DEFAULT_MINIMAL_OVERLAPPING_PERCENTAGE,
        shall_add_drone_to_notation: bool = True,
        add_sine_tone: bool = False,
        add_bends_before: bool = False,
    ):
        super().__init__(
            family_of_pitch_curves,
            minimal_overlapping_percentage=minimal_overlapping_percentage,
        )
        self._add_bends_before = add_bends_before
        self._shall_add_drone_to_notation = shall_add_drone_to_notation
        self._instrument_id = instrument_id
        self._instrument_ambitus = instrument_ambitus
        self._picker = ot3_converters.symmetrical.families.PickChordFromCurveAndWeightPairsConverter(
            self._instrument_ambitus, 1
        )
        self._dynamic_cycle = itertools.cycle("p".split(" "))
        self._duration_cycle = itertools.cycle((20, 15, 15))
        self._squash_in_cycle = itertools.cycle(
            (
                None,
                None,
                (0.25, events.basic.SimpleEvent(0.25)),
                None,
                (0.5, events.basic.SimpleEvent(0.25)),
                None,
            )
        )
        self._bend_interval_cycle = itertools.cycle((4, -4, 2, -3, -4))
        self._bend_interval_length_cycle = itertools.cycle((8, 5, 12, 7, 14, 10, 15))
        self._add_sine_tone = add_sine_tone

    def _make_blueprint_bracket(
        self,
        time_ranges: typing.Tuple[
            events.time_brackets.TimeRange, events.time_brackets.TimeRange
        ],
    ) -> events.time_brackets.TimeBracket:
        time_bracket = events.time_brackets.TimeBracket(
            [
                events.basic.TaggedSimultaneousEvent(
                    [events.basic.SequentialEvent([events.music.NoteLike([], 1)]),],
                    tag=self._instrument_id,
                )
            ],
            *time_ranges
        )
        return time_bracket

    def _get_time_ranges(
        self, start_time: parameters.abc.DurationType,
    ):
        duration = next(self._duration_cycle)
        time_ranges = (
            (start_time, start_time + 5),
            (start_time + duration, start_time + duration + 5),
        )
        return time_ranges

    def _get_bend_data(self, simple_event):
        return next(self._bend_interval_cycle), next(self._bend_interval_length_cycle)

    def convert(
        self, start_time: parameters.abc.DurationType,
    ) -> typing.Tuple[events.time_brackets.TimeBracket, ...]:
        time_ranges = self._get_time_ranges(start_time)
        resulting_time_brackets = []
        if self._are_curves_available_within_minimal_overlapping_percentage(
            time_ranges
        ):
            blueprint = self._make_blueprint_bracket(time_ranges)
            time_bracket_with_assigned_weight_curves = self._assign_curve_and_weight_pairs_on_events.convert(
                blueprint
            )
            converted_time_bracket = self._picker.convert(
                time_bracket_with_assigned_weight_curves
            )
            if not self._is_sequential_event_empty(converted_time_bracket[0][0]):
                if self._add_sine_tone:
                    resulting_time_brackets.extend(
                        self._make_copy_of_content_for_sine_tone(
                            start_time, converted_time_bracket
                        )
                    )

                squash_in_data = next(self._squash_in_cycle)
                if squash_in_data:
                    converted_time_bracket[0][0].squash_in(*squash_in_data)

                if self._add_bends_before:
                    for simple_event in converted_time_bracket[0][0]:
                        if (
                            hasattr(simple_event, "pitch_or_pitches")
                            and simple_event.pitch_or_pitches
                        ):
                            bend_interval, bend_length = self._get_bend_data(
                                simple_event
                            )
                            simple_event.playing_indicators.bend_before.bend_interval = (
                                bend_interval
                            )
                            simple_event.playing_indicators.bend_before.bend_length = (
                                bend_length
                            )

                self._add_cent_deviation(converted_time_bracket[0][0][:1])
                if self._shall_add_drone_to_notation:
                    self._add_drone_to_notation(converted_time_bracket)
                    if self._add_bends_before:
                        converted_time_bracket[1][0][
                            0
                        ].playing_indicators.empty_grace_container.is_active = True
                resulting_time_brackets.append(converted_time_bracket)

        return tuple(resulting_time_brackets)


class StartTimeToViolinGlissandiCalligraphicLineConverter(
    StartTimeToCalligraphicLineConverter
):
    def __init__(self, family_of_pitch_curves: events.families.FamilyOfPitchCurves):
        super().__init__(
            ot3_constants.instruments.ID_VIOLIN,
            family_of_pitch_curves,
            ot3_constants.instruments.AMBITUS_VIOLIN_JUST_INTONATION_PITCHES,
            minimal_overlapping_percentage=DEFAULT_MINIMAL_OVERLAPPING_PERCENTAGE,
            # shall_add_drone_to_notation=True,
            shall_add_drone_to_notation=False,
            add_sine_tone=True,
            add_bends_before=True,
        )

    def _get_bend_data(self, simple_event):
        if simple_event.pitch_or_pitches[0] < parameters.pitches.JustIntonationPitch(
            "5/3"
        ):
            return 4, 8
        else:
            return super()._get_bend_data(simple_event)


class StartTimeToViolinCalligraphicLineConverter(StartTimeToCalligraphicLineConverter):
    def __init__(self, family_of_pitch_curves: events.families.FamilyOfPitchCurves):
        super().__init__(
            ot3_constants.instruments.ID_VIOLIN,
            family_of_pitch_curves,
            ot3_constants.instruments.AMBITUS_VIOLIN_HARMONICS,
            minimal_overlapping_percentage=0.385,
            shall_add_drone_to_notation=False,
        )
        self._picker = (
            ot3_converters.symmetrical.families.PickViolinFlageolettFromCurveAndWeightPairsConverter()
        )
        self._duration_cycle = itertools.cycle((20, 15, 25))

    def convert(
        self, *args, **kwargs
    ) -> typing.Tuple[events.time_brackets.TimeBracket, ...]:
        time_brackets = super().convert(*args, **kwargs)
        for time_bracket in time_brackets:
            _add_copy_for_flageoletts_playing_suggestion(time_bracket)
        return time_brackets


class StartTimeToSaxophoneCalligraphicLineConverter(
    StartTimeToCalligraphicLineConverter
):
    def __init__(self, family_of_pitch_curves: events.families.FamilyOfPitchCurves):
        super().__init__(
            ot3_constants.instruments.ID_SAXOPHONE,
            family_of_pitch_curves,
            # ot3_constants.instruments.AMBITUS_SAXOPHONE_HARMONICS,
            ot3_constants.instruments.AMBITUS_SAXOPHONE_JUST_INTONATION_PITCHES,
            minimal_overlapping_percentage=0.7,
            shall_add_drone_to_notation=False,
        )
        # we don't use flageoletts
        # self._picker = (
        #     ot3_converters.symmetrical.families.PickSaxophoneFlageolettFromCurveAndWeightPairsConverter()
        # )
        self._duration_cycle = itertools.cycle((20, 15, 25))


class StartTimeToSaxophoneHarmonicsCalligraphicLineConverter(
    StartTimeToCalligraphicLineConverter
):
    def __init__(self, family_of_pitch_curves: events.families.FamilyOfPitchCurves):
        super().__init__(
            ot3_constants.instruments.ID_SAXOPHONE,
            family_of_pitch_curves,
            ot3_constants.instruments.AMBITUS_SAXOPHONE_HARMONICS,
            minimal_overlapping_percentage=0.7,
            shall_add_drone_to_notation=False,
        )
        self._picker = (
            ot3_converters.symmetrical.families.PickSaxophoneFlageolettFromCurveAndWeightPairsConverter()
        )
        self._duration_cycle = itertools.cycle((20, 15, 25))


class StartTimeToSaxophoneMultiphonicsConverter(StartTimeToCalligraphicLineConverter):
    def __init__(self, family_of_pitch_curves: events.families.FamilyOfPitchCurves):
        picker = (
            ot3_converters.symmetrical.families.PickSaxMultiphonicsFromCurveAndWeightPairsConverter()
        )
        super().__init__(
            ot3_constants.instruments.ID_SAXOPHONE,
            family_of_pitch_curves,
            picker.instrument_ambitus,
            minimal_overlapping_percentage=0,
            shall_add_drone_to_notation=False,
        )
        self._picker = picker
        self._duration_cycle = itertools.cycle((20, 15, 25))


class StartTimeToSaxophoneMelodicPhraseConverter(
    StartTimeToInstrumentTimeBracketsConverter
):
    def __init__(
        self, family_of_pitch_curves: events.families.FamilyOfPitchCurves,
    ):
        super().__init__(
            family_of_pitch_curves,
            minimal_overlapping_percentage=DEFAULT_MINIMAL_OVERLAPPING_PERCENTAGE,
        )
        self._instrument_id = ot3_constants.instruments.ID_SAXOPHONE
        self._instrument_ambitus = (
            ot3_constants.instruments.AMBITUS_SAXOPHONE_JUST_INTONATION_PITCHES
        )
        self._picker = ot3_converters.symmetrical.families.PickPitchLineFromCurveAndWeightPairsConverter(
            self._instrument_ambitus
        )
        self._dynamic_cycle = itertools.cycle("mp mf".split(" "))
        self._duration_cycle = itertools.cycle((15, 10))
        self._n_pitches_cycle = itertools.cycle((3,))
        self._rhythm_choice = generators.generic.DynamicChoice(
            (
                ot3_utilities.tools.make_gray_code_rhythm_cycle(3),
                ot3_utilities.tools.make_gray_code_rhythm_cycle(4),
            ),
            (
                expenvelope.Envelope.from_points((0, 1), (1, 0)),
                expenvelope.Envelope.from_points((0, 1), (1, 0)),
            ),
        )

    def _get_rhythm(
        self, absolute_entry_delay: parameters.abc.DurationType
    ) -> typing.Tuple[parameters.abc.DurationType, ...]:
        absolute_position = (
            absolute_entry_delay / ot3_constants.families_pitch.FAMILIES_PITCH.duration
        )
        return next(self._rhythm_choice.gamble_at(absolute_position))

    def _make_blueprint_bracket(
        self,
        time_ranges: typing.Tuple[
            events.time_brackets.TimeRange, events.time_brackets.TimeRange
        ],
        absolute_entry_delay: parameters.abc.DurationType,
    ) -> events.time_brackets.TimeBracket:
        dynamic = next(self._dynamic_cycle)
        time_bracket = events.time_brackets.TimeBracket(
            [
                events.basic.TaggedSimultaneousEvent(
                    [
                        events.basic.SequentialEvent(
                            [
                                events.music.NoteLike([], rhythm, dynamic)
                                for rhythm in self._get_rhythm(absolute_entry_delay)
                            ]
                        ),
                    ],
                    tag=self._instrument_id,
                )
            ],
            *time_ranges
        )
        return time_bracket

    def _get_time_ranges(
        self, start_time: parameters.abc.DurationType,
    ):
        duration = next(self._duration_cycle)
        time_ranges = (
            (start_time, start_time + 10),
            (start_time + duration + 5, start_time + duration + 10),
        )
        return time_ranges

    def convert(
        self, start_time: parameters.abc.DurationType,
    ) -> typing.Tuple[events.time_brackets.TimeBracket, ...]:
        time_ranges = self._get_time_ranges(start_time)
        resulting_time_brackets = []
        if self._are_curves_available_within_minimal_overlapping_percentage(
            time_ranges
        ):
            blueprint = self._make_blueprint_bracket(time_ranges, start_time)
            time_bracket_with_assigned_weight_curves = self._assign_curve_and_weight_pairs_on_events.convert(
                blueprint
            )
            converted_time_bracket = self._picker.convert(
                time_bracket_with_assigned_weight_curves
            )
            if not self._is_sequential_event_empty(converted_time_bracket[0][0]):
                resulting_time_brackets.extend(
                    self._make_copy_of_content_for_sine_tone(
                        start_time, converted_time_bracket, True
                    )
                )
                converted_time_bracket[0][0].tie_by(
                    lambda ev0, ev1: ev0.pitch_or_pitches == ev1.pitch_or_pitches
                )
                resulting_time_brackets.append(converted_time_bracket)

        return tuple(resulting_time_brackets)


class StartTimeToHarmonicMelodicPhraseConverter(
    StartTimeToInstrumentTimeBracketsConverter
):
    def __init__(
        self,
        instrument_id: str,
        family_of_pitch_curves: events.families.FamilyOfPitchCurves,
        instrument_ambitus: ot3_parameters.ambitus.Ambitus,
        instrument: ot3_parameters.spectrals.StringInstrument,
        minimal_overlapping_percentage: float = 0.4,
        seed: int = 12,
    ):
        super().__init__(
            family_of_pitch_curves,
            minimal_overlapping_percentage=minimal_overlapping_percentage,
            seed=seed,
        )
        self._instrument_id = instrument_id
        self._instrument_ambitus = instrument_ambitus
        self._instrument = instrument
        self._picker = ot3_converters.symmetrical.families.PickHarmonicsPitchLineFromCurveAndWeightPairsConverter(
            self._instrument_ambitus, self._instrument
        )
        self._dynamic_cycle = itertools.cycle("mf mp".split(" "))
        self._duration_cycle = itertools.cycle((15, 25, 20))
        self._n_pitches_cycle = itertools.cycle((3,))
        self._rhythm_choice = generators.generic.DynamicChoice(
            (
                ot3_utilities.tools.make_gray_code_rhythm_cycle(3),
                ot3_utilities.tools.make_gray_code_rhythm_cycle(4),
            ),
            (
                expenvelope.Envelope.from_points(
                    (0, 1), (0.5, 0), (0.75, 0.25), (1, 1)
                ),
                expenvelope.Envelope.from_points((0, 1), (0.5, 1), (0.75, 1), (1, 0)),
            ),
        )

    def _get_rhythm(
        self, absolute_entry_delay: parameters.abc.DurationType
    ) -> typing.Tuple[parameters.abc.DurationType, ...]:
        absolute_position = (
            absolute_entry_delay / ot3_constants.families_pitch.FAMILIES_PITCH.duration
        )
        return next(self._rhythm_choice.gamble_at(absolute_position))

    def _make_blueprint_bracket(
        self,
        time_ranges: typing.Tuple[
            events.time_brackets.TimeRange, events.time_brackets.TimeRange
        ],
        absolute_entry_delay: parameters.abc.DurationType,
    ) -> events.time_brackets.TimeBracket:
        dynamic = next(self._dynamic_cycle)
        time_bracket = events.time_brackets.TimeBracket(
            [
                events.basic.TaggedSimultaneousEvent(
                    [
                        events.basic.SequentialEvent(
                            [
                                events.music.NoteLike([], rhythm, dynamic)
                                for rhythm in self._get_rhythm(absolute_entry_delay)
                            ]
                        ),
                    ],
                    tag=self._instrument_id,
                )
            ],
            *time_ranges
        )
        return time_bracket

    def _get_time_ranges(
        self, start_time: parameters.abc.DurationType,
    ):
        duration = next(self._duration_cycle)
        time_ranges = (
            (start_time, start_time + 5),
            (start_time + duration, start_time + duration + 5),
        )
        return time_ranges

    def convert(
        self, start_time: parameters.abc.DurationType,
    ) -> typing.Tuple[events.time_brackets.TimeBracket, ...]:
        time_ranges = self._get_time_ranges(start_time)
        resulting_time_brackets = []
        if self._are_curves_available_within_minimal_overlapping_percentage(
            time_ranges
        ):
            blueprint = self._make_blueprint_bracket(time_ranges, start_time)
            time_bracket_with_assigned_weight_curves = self._assign_curve_and_weight_pairs_on_events.convert(
                blueprint
            )
            converted_time_bracket = self._picker.convert(
                time_bracket_with_assigned_weight_curves
            )
            if not self._is_sequential_event_empty(converted_time_bracket[0][0]):
                resulting_time_brackets.extend(
                    self._make_copy_of_content_for_sine_tone(
                        start_time, converted_time_bracket, for_repetition=True
                    )
                )
                converted_time_bracket[0][0].tie_by(
                    lambda ev0, ev1: ev0.pitch_or_pitches == ev1.pitch_or_pitches
                )
                _add_copy_for_flageoletts_playing_suggestion(converted_time_bracket)
                resulting_time_brackets.append(converted_time_bracket)

        return tuple(resulting_time_brackets)


class StartTimeToViolinMelodicPhraseConverter(
    StartTimeToInstrumentTimeBracketsConverter
):
    def __init__(
        self, family_of_pitch_curves: events.families.FamilyOfPitchCurves,
    ):
        super().__init__(
            family_of_pitch_curves, minimal_overlapping_percentage=0.85,
        )
        self._instrument_id = ot3_constants.instruments.ID_VIOLIN
        self._instrument_ambitus = (
            ot3_constants.instruments.AMBITUS_VIOLIN_JUST_INTONATION_PITCHES
        )
        self._picker = ot3_converters.symmetrical.families.PickPitchLineFromCurveAndWeightPairsConverter(
            self._instrument_ambitus
        )
        self._dynamic_cycle = itertools.cycle("mp mf".split(" "))
        self._duration_cycle = itertools.cycle((15, 10))
        self._rhythm_choice = generators.generic.DynamicChoice(
            (
                ot3_utilities.tools.make_gray_code_rhythm_cycle(4),
                ot3_utilities.tools.make_gray_code_rhythm_cycle(5),
            ),
            (
                expenvelope.Envelope.from_points((0, 1), (1, 0)),
                expenvelope.Envelope.from_points((0, 1), (1, 0)),
            ),
        )

    def _get_rhythm(
        self, absolute_entry_delay: parameters.abc.DurationType
    ) -> typing.Tuple[parameters.abc.DurationType, ...]:
        absolute_position = (
            absolute_entry_delay / ot3_constants.families_pitch.FAMILIES_PITCH.duration
        )
        return next(self._rhythm_choice.gamble_at(absolute_position))

    def _make_blueprint_bracket(
        self,
        time_ranges: typing.Tuple[
            events.time_brackets.TimeRange, events.time_brackets.TimeRange
        ],
        absolute_entry_delay: parameters.abc.DurationType,
    ) -> events.time_brackets.TimeBracket:
        dynamic = next(self._dynamic_cycle)
        time_bracket = events.time_brackets.TimeBracket(
            [
                events.basic.TaggedSimultaneousEvent(
                    [
                        events.basic.SequentialEvent(
                            [
                                events.music.NoteLike([], rhythm, dynamic)
                                for rhythm in self._get_rhythm(absolute_entry_delay)
                            ]
                        ),
                    ],
                    tag=self._instrument_id,
                )
            ],
            *time_ranges
        )
        return time_bracket

    def _get_time_ranges(
        self, start_time: parameters.abc.DurationType,
    ):
        duration = next(self._duration_cycle)
        time_ranges = (
            (start_time, start_time + 10),
            (start_time + duration + 5, start_time + duration + 10),
        )
        return time_ranges

    def convert(
        self, start_time: parameters.abc.DurationType,
    ) -> typing.Tuple[events.time_brackets.TimeBracket, ...]:
        time_ranges = self._get_time_ranges(start_time)
        resulting_time_brackets = []
        if self._are_curves_available_within_minimal_overlapping_percentage(
            time_ranges
        ):
            blueprint = self._make_blueprint_bracket(time_ranges, start_time)
            time_bracket_with_assigned_weight_curves = self._assign_curve_and_weight_pairs_on_events.convert(
                blueprint
            )
            converted_time_bracket = self._picker.convert(
                time_bracket_with_assigned_weight_curves
            )
            if not self._is_sequential_event_empty(converted_time_bracket[0][0]):
                resulting_time_brackets.extend(
                    self._make_copy_of_content_for_sine_tone(
                        start_time, converted_time_bracket, True
                    )
                )
                converted_time_bracket[0][0].tie_by(
                    lambda ev0, ev1: ev0.pitch_or_pitches == ev1.pitch_or_pitches
                )
                self._add_cent_deviation(converted_time_bracket[0][0])
                resulting_time_brackets.append(converted_time_bracket)

        return tuple(resulting_time_brackets)


class StartTimeToInstrumentalNoiseConverter(StartTimeToInstrumentTimeBracketsConverter):
    def __init__(
        self, instrument_id: str,
    ):
        super().__init__(None, None)
        self._instrument_id = instrument_id
        self._dynamic_cycle = itertools.cycle("mf".split(" "))
        self._duration_cycle = itertools.cycle((10, 15, 10))
        self._presence_cycle = itertools.cycle((2, 0, 1, 0, 1))
        self._density_cycle = itertools.cycle((2, 3, 0, 1, 2, 3, 1, 0))

    def _make_blueprint_bracket(
        self,
        time_ranges: typing.Tuple[
            events.time_brackets.TimeRange, events.time_brackets.TimeRange
        ],
    ) -> events.time_brackets.TimeBracket:
        dynamic = next(self._dynamic_cycle)
        time_bracket = events.time_brackets.TimeBracket(
            [
                events.basic.TaggedSimultaneousEvent(
                    [
                        events.basic.SequentialEvent(
                            [
                                ot3_events.noises.Noise(
                                    next(self._density_cycle),
                                    next(self._presence_cycle),
                                    1,
                                    parameters.volumes.WesternVolume(dynamic),
                                )
                            ]
                        ),
                    ],
                    tag=self._instrument_id,
                )
            ],
            *time_ranges
        )
        return time_bracket

    def _get_time_ranges(
        self, start_time: parameters.abc.DurationType,
    ):
        duration = next(self._duration_cycle)
        time_ranges = (
            (start_time, start_time + 5),
            (start_time + duration, start_time + duration + 5),
        )
        return time_ranges

    def convert(
        self, start_time: parameters.abc.DurationType,
    ) -> typing.Tuple[events.time_brackets.TimeBracket, ...]:
        time_ranges = self._get_time_ranges(start_time)
        resulting_time_brackets = [self._make_blueprint_bracket(time_ranges)]
        return tuple(resulting_time_brackets)


class StartTimeToSaxNoiseConverter(StartTimeToInstrumentTimeBracketsConverter):
    def __init__(self):
        super().__init__(None, None)
        self._instrument_id = ot3_constants.instruments.ID_SAXOPHONE
        self._dynamic_cycle = itertools.cycle("f".split(" "))
        self._duration_cycle = itertools.cycle((15, 20, 25))
        self._density_cycle = itertools.cycle((0, 1))

    def _make_blueprint_bracket(
        self,
        time_ranges: typing.Tuple[
            events.time_brackets.TimeRange, events.time_brackets.TimeRange
        ],
    ) -> events.time_brackets.TimeBracket:
        dynamic = next(self._dynamic_cycle)
        time_bracket = events.time_brackets.TimeBracket(
            [
                events.basic.TaggedSimultaneousEvent(
                    [
                        events.basic.SequentialEvent(
                            [
                                ot3_events.noises.SaxNoise(
                                    next(self._density_cycle),
                                    1,
                                    parameters.volumes.WesternVolume(dynamic),
                                )
                            ]
                        ),
                    ],
                    tag=self._instrument_id,
                )
            ],
            *time_ranges
        )
        return time_bracket

    def _get_time_ranges(
        self, start_time: parameters.abc.DurationType,
    ):
        duration = next(self._duration_cycle)
        time_ranges = (
            (start_time, start_time + 5),
            (start_time + duration, start_time + duration + 10),
        )
        return time_ranges

    def convert(
        self, start_time: parameters.abc.DurationType,
    ) -> typing.Tuple[events.time_brackets.TimeBracket, ...]:
        time_ranges = self._get_time_ranges(start_time)
        resulting_time_brackets = [self._make_blueprint_bracket(time_ranges)]
        return tuple(resulting_time_brackets)


class StartTimeToBowNoiseConverter(StartTimeToInstrumentalNoiseConverter):
    def __init__(self):
        super().__init__(ot3_constants.instruments.ID_VIOLIN)
        self._dynamic_cycle = itertools.cycle("mp".split(" "))
        self._duration_cycle = itertools.cycle((10, 15, 10))

    def _make_blueprint_bracket(
        self,
        time_ranges: typing.Tuple[
            events.time_brackets.TimeRange, events.time_brackets.TimeRange
        ],
    ) -> events.time_brackets.TimeBracket:
        dynamic = next(self._dynamic_cycle)
        event = events.music.NoteLike("b", 1, dynamic)
        event.playing_indicators.bow_noise.is_active = True
        time_bracket = events.time_brackets.TimeBracket(
            [
                events.basic.TaggedSimultaneousEvent(
                    [events.basic.SequentialEvent([event]),], tag=self._instrument_id,
                )
            ],
            *time_ranges
        )
        return time_bracket


class StartTimeToTeethOnReedConverter(StartTimeToInstrumentalNoiseConverter):
    def __init__(self):
        super().__init__(ot3_constants.instruments.ID_SAXOPHONE)
        self._dynamic_cycle = itertools.cycle("mp".split(" "))
        self._duration_cycle = itertools.cycle((15, 20, 20))

    def _make_blueprint_bracket(
        self,
        time_ranges: typing.Tuple[
            events.time_brackets.TimeRange, events.time_brackets.TimeRange
        ],
    ) -> events.time_brackets.TimeBracket:
        dynamic = next(self._dynamic_cycle)
        event = events.music.NoteLike("c", 5, dynamic)
        event.playing_indicators.teeth_on_reed.is_active = True
        time_bracket = events.time_brackets.TimeBracket(
            [
                events.basic.TaggedSimultaneousEvent(
                    [events.basic.SequentialEvent([event]),], tag=self._instrument_id,
                )
            ],
            *time_ranges
        )
        return time_bracket


class StartTimeToHarmonicGlissandoConverter(StartTimeToInstrumentalNoiseConverter):
    def __init__(self):
        super().__init__(ot3_constants.instruments.ID_VIOLIN)
        self._dynamic_cycle = itertools.cycle("pp".split(" "))
        self._duration_cycle = itertools.cycle((10, 15, 10))

    def _make_blueprint_bracket(
        self,
        time_ranges: typing.Tuple[
            events.time_brackets.TimeRange, events.time_brackets.TimeRange
        ],
    ) -> events.time_brackets.TimeBracket:
        dynamic = next(self._dynamic_cycle)
        event = events.music.NoteLike("b", 1, dynamic)
        event.playing_indicators.harmonic_glissando.is_active = True
        time_bracket = events.time_brackets.TimeBracket(
            [
                events.basic.TaggedSimultaneousEvent(
                    [events.basic.SequentialEvent([event]),], tag=self._instrument_id,
                )
            ],
            *time_ranges
        )
        return time_bracket
