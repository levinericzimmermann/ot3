import typing

import quicktions as fractions

from mutwo import converters
from mutwo import events
from mutwo import parameters
from mutwo import utilities

from ot3 import constants as ot3_constants


class WestminsterPhrase(events.basic.SequentialEvent):
    def __init__(
        self,
        events: typing.Sequence[events.music.NoteLike],
        tempo: parameters.tempos.TempoPoint,
        start_time: parameters.abc.DurationType,
    ):
        super().__init__(events)
        self.tempo = tempo
        self.start_time = start_time

    @property
    def duration_in_seconds(self) -> parameters.abc.DurationType:
        return (
            converters.symmetrical.tempos.TempoPointConverter().convert(self.tempo)
            * self.duration
            * 4
        )

    @property
    def end_time(self) -> parameters.abc.DurationType:
        return self.start_time + self.duration_in_seconds


class WestminsterPhraseToTimeBracketsConverter(converters.abc.Converter):
    def convert(
        self, westminster_phrase_to_convert: WestminsterPhrase
    ) -> typing.Tuple[events.time_brackets.TimeBracket, ...]:
        sequential_event_for_sax = events.basic.SequentialEvent(
            tuple(westminster_phrase_to_convert)
        )
        # saxophone should always play subtones when playing the
        # westminster melody
        sequential_event_for_sax[0].notation_indicators.markup.content = (
            "\\tiny { subtone }"
        )
        sequential_event_for_sax[0].notation_indicators.markup.direction = "up"
        sequential_event_for_sax[-1].playing_indicators.fermata.fermata_type = "fermata"
        for nth_simple_event, simple_event in enumerate(sequential_event_for_sax):
            if nth_simple_event != 0 and nth_simple_event % 4 == 0:
                simple_event.playing_indicators.breath_mark.is_active = True

        time_bracket = events.time_brackets.TempoBasedTimeBracket(
            [
                events.basic.TaggedSimultaneousEvent(
                    [sequential_event_for_sax],
                    tag=ot3_constants.instruments.ID_SAXOPHONE,
                )
            ],
            start_or_start_range=westminster_phrase_to_convert.start_time,
            end_or_end_range=westminster_phrase_to_convert.end_time,
            tempo=westminster_phrase_to_convert.tempo,
        )
        return (time_bracket,)


class WestminsterMelodiesToTimeBracketsConverter(converters.abc.Converter):
    def __init__(
        self,
        families_pitch: events.basic.SequentialEvent[
            typing.Union[events.basic.SimpleEvent, events.families.FamilyOfPitchCurves]
        ],
        delay_until_first_westminster_phrase_starts: parameters.abc.DurationType = 60,
        duration_for_all_westminster_phrases: parameters.abc.DurationType = 60 * 50,
    ):
        self._families_pitch = families_pitch
        self._delay_until_first_westminster_phrase_starts = (
            delay_until_first_westminster_phrase_starts
        )
        self._duration_for_all_westminster_phrases = (
            duration_for_all_westminster_phrases
        )

    def _estimate_start_positions_for_each_westminster_phrase(
        self,
        westminster_melodies_to_convert: events.basic.SequentialEvent[
            events.basic.SequentialEvent[events.music.NoteLike]
        ],
    ) -> typing.Tuple[parameters.abc.DurationType, ...]:
        n_phrases = len(westminster_melodies_to_convert)
        equal_time_step = self._duration_for_all_westminster_phrases / n_phrases
        positions = tuple(
            utilities.tools.accumulate_from_n(
                [equal_time_step] * n_phrases,
                self._delay_until_first_westminster_phrase_starts,
            )
        )
        return positions

    def _get_tempo_for_each_westminster_phrase(
        self,
        westminster_melodies_to_convert: events.basic.SequentialEvent[
            events.basic.SequentialEvent[events.music.NoteLike]
        ],
    ) -> typing.Tuple[parameters.tempos.TempoPoint, ...]:
        tempo_points = []
        n_westminster_melodies_to_convert = len(westminster_melodies_to_convert)
        for nth_westminster_melody, _ in enumerate(westminster_melodies_to_convert):
            tempo = int(
                ot3_constants.westminster.TEMPO_ENVELOPE.value_at(
                    nth_westminster_melody / n_westminster_melodies_to_convert
                )
            )
            tempo_points.append(parameters.tempos.TempoPoint(tempo))
        return tuple(tempo_points)

    def _make_westminster_phrases(
        self,
        westminster_melodies_to_convert: events.basic.SequentialEvent[
            events.basic.SequentialEvent[events.music.NoteLike]
        ],
    ) -> typing.Tuple[WestminsterPhrase, ...]:
        start_position_per_phrase = self._estimate_start_positions_for_each_westminster_phrase(
            westminster_melodies_to_convert
        )
        tempo_per_phrase = self._get_tempo_for_each_westminster_phrase(
            westminster_melodies_to_convert
        )
        westminster_phrases = []
        for start_position, tempo, phrase in zip(
            start_position_per_phrase, tempo_per_phrase, westminster_melodies_to_convert
        ):
            westminster_phrase = WestminsterPhrase(phrase[:], tempo, start_position)
            westminster_phrases.append(westminster_phrase)
        return tuple(westminster_phrases)

    def _redistribute_westminster_phrases(
        self, westminster_phrases: typing.Tuple[WestminsterPhrase, ...],
    ):
        start_and_end_time_for_each_family_event = (
            self._families_pitch.start_and_end_time_per_event
        )
        for westminster_phrase in westminster_phrases:
            simultaneous_familiy_event_index = self._families_pitch.get_event_index_at(
                westminster_phrase.start_time
            )
            if simultaneous_familiy_event_index is not None:
                if isinstance(
                    self._families_pitch[simultaneous_familiy_event_index],
                    events.basic.SimpleEvent,
                ):
                    event_index_to_center = simultaneous_familiy_event_index
                else:
                    event_index_to_center = simultaneous_familiy_event_index + 1

                try:
                    start, end = start_and_end_time_for_each_family_event[
                        event_index_to_center
                    ]
                except IndexError:
                    start = None
            else:
                simultaneous_familiy_event_index = len(self._families_pitch) - 1
                start = None

            if start is not None:
                center = (end + start) / 2
                westminster_phrase.start_time = center - (
                    westminster_phrase.duration / 2
                )

            else:
                westminster_phrase.start_time = (
                    start_and_end_time_for_each_family_event[
                        simultaneous_familiy_event_index
                    ][-1]
                    + 15
                )

    def _convert_westminster_phrases_to_time_brackets(
        self, westminster_phrases_to_convert: typing.Tuple[WestminsterPhrase, ...],
    ) -> typing.Tuple[events.time_brackets.TimeBracket, ...]:
        westminster_phrase_to_time_brackets_converter = (
            WestminsterPhraseToTimeBracketsConverter()
        )
        time_brackets = []
        for westminster_phrase in westminster_phrases_to_convert:
            time_brackets.extend(
                westminster_phrase_to_time_brackets_converter.convert(
                    westminster_phrase
                )
            )
        return tuple(time_brackets)

    def convert(
        self,
        westminster_melodies_to_convert: events.basic.SequentialEvent[
            events.basic.SequentialEvent[events.music.NoteLike]
        ],
    ) -> typing.Tuple[events.time_brackets.TimeBracket, ...]:
        westminster_phrases = self._make_westminster_phrases(
            westminster_melodies_to_convert
        )
        self._redistribute_westminster_phrases(westminster_phrases)
        time_brackets = self._convert_westminster_phrases_to_time_brackets(
            westminster_phrases
        )
        last_time_bracket = time_brackets[-1]
        last_time_bracket[0][0][-1].duration += fractions.Fraction(1, 1)
        last_time_bracket[0][0][-1].playing_indicators.fermata.fermata_type = (
            "longfermata"
        )
        return time_brackets
