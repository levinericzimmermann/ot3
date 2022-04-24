import typing

import numpy as np

from mutwo import converters
from mutwo import events
from mutwo import generators
from mutwo import parameters

from ot3 import constants as ot3_constants
from ot3 import utilities as ot3_utilities


class FamiliesPitchToModesConverter(converters.abc.Converter):
    def __init__(self, seed: int = 200):
        self._random = np.random.default_rng(seed)

    def _find_position_spans(
        self,
        families_pitch: events.basic.SequentialEvent[
            typing.Union[events.basic.SimpleEvent, events.families.FamilyOfPitchCurves]
        ],
    ) -> typing.Tuple[
        typing.Tuple[parameters.abc.DurationType, parameters.abc.DurationType], ...
    ]:
        position_spans_for_triads = []

        duration_of_families_pitch = families_pitch.duration
        for start_and_end_time, event in zip(
            families_pitch.start_and_end_time_per_event, families_pitch
        ):
            if isinstance(event, events.basic.SimpleEvent):
                start_time = start_and_end_time[0]
                absolute_position = start_time / duration_of_families_pitch
                shall_add_triad_likelihood = ot3_constants.modes.LIKELIHOOD_TO_ADD_TRIAD_TO_REST.value_at(
                    absolute_position
                )
                if self._random.uniform(0, 1) < shall_add_triad_likelihood:
                    position_spans_for_triads.append(start_and_end_time)

        return tuple(position_spans_for_triads)

    def _add_triads_to_mode_events(
        self,
        mode_events: typing.Tuple[
            events.basic.SequentialEvent[events.basic.SimpleEvent]
        ],
        families_pitch: events.basic.SequentialEvent[
            typing.Union[events.basic.SimpleEvent, events.families.FamilyOfPitchCurves]
        ],
    ):

        position_spans_for_triads = self._find_position_spans(families_pitch)
        n_triads = len(position_spans_for_triads)

        triad_per_position_span = ot3_utilities.tools.not_fibonacci_transition(
            *generators.toussaint.euclidean(n_triads, 2),
            ot3_constants.modes.TRIAD0,
            ot3_constants.modes.TRIAD1,
        )

        for nth_triad, triad, position_span in zip(
            range(n_triads), triad_per_position_span, position_spans_for_triads
        ):
            triad_absolut_position = nth_triad / n_triads
            max_span = position_span[1] - position_span[0]
            max_span_size_for_current_tendency = (
                ot3_constants.modes.SPAN_SIZE_TENDENCY.range_at(triad_absolut_position)[
                    1
                ]
                * max_span
            )
            relative_min_span_start = (
                max_span - max_span_size_for_current_tendency
            ) / 2

            for mode_event in mode_events:
                span_size_as_factor = ot3_constants.modes.SPAN_SIZE_TENDENCY.value_at(
                    triad_absolut_position
                )
                span_size = max_span * span_size_as_factor
                free_space = max_span_size_for_current_tendency - span_size
                start = (
                    relative_min_span_start
                    + self._random.uniform(0, free_space)
                    + position_span[0]
                )

                note = events.music.NoteLike(
                    [
                        pitch + parameters.pitches.JustIntonationPitch("2/1")
                        for pitch in triad
                    ],
                    span_size,
                    "mp",
                )
                mode_event.squash_in(start, note)

    def _convert_sequential_mode_event_to_time_brackets(
        self, nth_mode: int, sequential_event: events.basic.SequentialEvent
    ) -> typing.Tuple[events.time_brackets.TimeBracket, ...]:
        time_brackets = []
        tag = f"mode_{nth_mode}"
        for absolute_time, event in zip(
            sequential_event.absolute_times, sequential_event
        ):
            if hasattr(event, "pitch_or_pitches"):
                time_bracket = events.time_brackets.TimeBracket(
                    [
                        events.basic.TaggedSimultaneousEvent(
                            [events.basic.SequentialEvent([event])], tag=tag
                        )
                    ],
                    start_or_start_range=absolute_time,
                    end_or_end_range=absolute_time + event.duration,
                )
                time_brackets.append(time_bracket)
        return tuple(time_brackets)

    def convert(
        self,
        families_pitch: events.basic.SequentialEvent[
            typing.Union[events.basic.SimpleEvent, events.families.FamilyOfPitchCurves]
        ],
    ) -> typing.Tuple[events.time_brackets.TimeBracket, ...]:
        mode_events = tuple(
            events.basic.SequentialEvent(
                [events.basic.SimpleEvent(families_pitch.duration)]
            )
            for _ in range(ot3_constants.modes.N_VOICES)
        )

        self._add_triads_to_mode_events(mode_events, families_pitch)

        time_brackets = []
        for nth_mode, sequential_event in enumerate(mode_events):
            time_brackets.extend(
                self._convert_sequential_mode_event_to_time_brackets(
                    nth_mode, sequential_event
                )
            )

        return tuple(time_brackets)
