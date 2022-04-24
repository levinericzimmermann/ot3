"""Shadows of westminster melodies"""

import typing

from mutwo import converters
from mutwo import events
from mutwo import parameters


ExtractedEvent = typing.Tuple[
    parameters.abc.DurationType, events.basic.TaggedSimultaneousEvent
]
ExtractedEvents = typing.Tuple[
    ExtractedEvent,
    ...,
]


class TimeBracketContainerToShadowsConverter(converters.abc.Converter):
    def __init__(
        self, time_bracket_container: events.time_brackets.TimeBracketContainer
    ):
        self._tempo_based_time_brackets = self._extract_tempo_based_time_brackets(
            time_bracket_container
        )

    def _extract_tempo_based_time_brackets(
        self, time_bracket_container: events.time_brackets.TimeBracketContainer
    ) -> typing.Tuple[events.time_brackets.TempoBasedTimeBracket, ...]:
        tempo_based_time_brackets = filter(
            lambda time_bracket: isinstance(
                time_bracket, events.time_brackets.TempoBasedTimeBracket
            ),
            iter(time_bracket_container),
        )
        return tuple(tempo_based_time_brackets)

    def _extract_tagged_events_with_given_tag(self, tag: str) -> ExtractedEvents:
        extracted_events = []
        for tempo_based_time_bracket in self._tempo_based_time_brackets:
            extracted_event = None
            for tagged_event in tempo_based_time_bracket:
                if tagged_event.tag == tag:
                    extracted_event = tagged_event
                    break
            if extracted_event:
                start_time = tempo_based_time_bracket.minimal_start
                copied_event = extracted_event.copy()
                copied_event.duration = tempo_based_time_bracket.duration
                extracted_events.append((start_time, copied_event))

        return tuple(extracted_events)

    def _concatenate_extracted_events(
        self, extracted_events: ExtractedEvents
    ) -> events.basic.SequentialEvent:
        concatenated_events = events.basic.SequentialEvent(
            [
            ]
        )
        for global_delay, extracted_event in extracted_events:
            for local_delay, simple_event in zip(
                extracted_event[0].absolute_times, extracted_event[0]
            ):
                concatenated_delay = global_delay + local_delay
                difference = concatenated_delay - concatenated_events.duration
                if difference > 0:
                    concatenated_events.append(events.basic.SimpleEvent(difference))
                concatenated_events.append(simple_event)
        return concatenated_events

    def convert(self, tag_of_voice: str) -> events.basic.SequentialEvent:
        tagged_events_with_given_tag = self._extract_tagged_events_with_given_tag(
            tag_of_voice
        )
        concatenated_extracted_events = self._concatenate_extracted_events(
            tagged_events_with_given_tag
        )
        return concatenated_extracted_events


class TimeBracketContainerToFifthParallelShadowsConverter(
    TimeBracketContainerToShadowsConverter
):
    def convert(self, tag_of_voice: str) -> events.basic.SequentialEvent:
        def mutate_pitch_or_pitches(
            pitch_or_pitches: typing.Optional[
                typing.Sequence[parameters.pitches.JustIntonationPitch]
            ],
        ):
            if pitch_or_pitches is not None:
                return [
                    pitch + parameters.pitches.JustIntonationPitch("3/2")
                    for pitch in pitch_or_pitches
                ]
            else:
                return

        concatenated_extracted_events = super().convert(tag_of_voice)
        concatenated_extracted_events.set_parameter(
            "pitch_or_pitches",
            mutate_pitch_or_pitches,
        )
        return concatenated_extracted_events
