import abc
import typing

import abjad  # type: ignore
from abjadext import nauert  # type: ignore
import expenvelope

from mutwo.converters import abc as converters_abc
from mutwo.converters.frontends import abjad as mutwo_abjad
from mutwo.converters.frontends import abjad_process_container_routines
from mutwo import events
from mutwo import parameters

from ot3.constants import concert_pitch
from ot3.constants import instruments
from ot3.converters.frontends import abjad_constants as ot3_abjad_constants
from ot3.converters.frontends import (
    abjad_process_container_routines as ot3_abjad_process_container_routines,
)

ADD_TIME_BRACKET_MARKS = True
ADD_TICKS = False


class ViolinSequentialEventToAbjadVoiceConverter(
    mutwo_abjad.SequentialEventToAbjadVoiceConverter
):
    """Simple inherited class to add ottava marks"""

    _abjad_pitch_border = abjad.NamedPitch("c'''")
    _ji_pitch_border = parameters.pitches.JustIntonationPitch("4/1")

    def _adjust_abjad_pitch_by_ottava(
        self, abjad_pitch: abjad.NamedPitch, n_octaves: int
    ) -> abjad.NamedPitch:
        return abjad.NamedPitch(
            abjad_pitch.name,
            octave=abjad_pitch.octave.number + n_octaves,
        )

    def _are_octaves(
        self, abjad_pitch0: abjad.NamedPitch, abjad_pitch1: abjad.NamedPitch
    ) -> bool:
        return abs((abjad_pitch1 - abjad_pitch0).semitones) == 12

    def convert(
        self, sequential_event_to_convert: events.basic.SequentialEvent
    ) -> abjad.Voice:
        pitch_or_pitches_per_event = sequential_event_to_convert.get_parameter(
            "pitch_or_pitches"
        )
        add_octava = False
        for simple_event, pitch_or_pitches in zip(
            sequential_event_to_convert, pitch_or_pitches_per_event
        ):
            if pitch_or_pitches:
                test_pitches = True
                if hasattr(simple_event, "playing_indicators"):
                    if (
                        simple_event.playing_indicators.precise_double_harmonic.string_pitch0
                        is not None
                    ):
                        test_pitches = False
                        if (
                            simple_event.playing_indicators.precise_double_harmonic.played_pitch0
                            > self._abjad_pitch_border
                            or simple_event.playing_indicators.precise_double_harmonic.played_pitch1
                            > self._abjad_pitch_border
                        ) and not (
                            self._are_octaves(
                                simple_event.playing_indicators.precise_double_harmonic.played_pitch0,
                                simple_event.playing_indicators.precise_double_harmonic.string_pitch0,
                            )
                            or self._are_octaves(
                                simple_event.playing_indicators.precise_double_harmonic.played_pitch1,
                                simple_event.playing_indicators.precise_double_harmonic.string_pitch1,
                            )
                        ):
                            add_octava = True
                            break
                    elif (
                        simple_event.playing_indicators.precise_natural_harmonic.string_pitch
                        is not None
                    ):
                        test_pitches = False
                        if simple_event.playing_indicators.precise_natural_harmonic.played_pitch > self._abjad_pitch_border and not self._are_octaves(
                            simple_event.playing_indicators.precise_natural_harmonic.played_pitch,
                            simple_event.playing_indicators.precise_natural_harmonic.string_pitch,
                        ):
                            add_octava = True
                            break

                if test_pitches:
                    for pitch in pitch_or_pitches:
                        if pitch > self._ji_pitch_border:
                            add_octava = True
                            break
        if add_octava:
            adjust_n_octave = 1
            for nth_event, event in enumerate(sequential_event_to_convert):
                if not hasattr(event, "notation_indicators"):
                    event = events.music.NoteLike([], event.duration)
                event.notation_indicators.ottava.n_octaves = adjust_n_octave
                if event.playing_indicators.precise_natural_harmonic.string_pitch:
                    event.playing_indicators.precise_natural_harmonic.string_pitch = self._adjust_abjad_pitch_by_ottava(
                        event.playing_indicators.precise_natural_harmonic.string_pitch,
                        adjust_n_octave,
                    )

                if event.playing_indicators.precise_double_harmonic.string_pitch0:
                    event.playing_indicators.precise_double_harmonic.string_pitch0 = self._adjust_abjad_pitch_by_ottava(
                        event.playing_indicators.precise_double_harmonic.string_pitch0,
                        adjust_n_octave,
                    )
                    event.playing_indicators.precise_double_harmonic.string_pitch1 = self._adjust_abjad_pitch_by_ottava(
                        event.playing_indicators.precise_double_harmonic.string_pitch0,
                        adjust_n_octave,
                    )

                sequential_event_to_convert[nth_event] = event

        return super().convert(sequential_event_to_convert)


class TimeBracketToAbjadScoreConverter(
    mutwo_abjad.NestedComplexEventToAbjadContainerConverter
):
    def __init__(
        self,
        nested_complex_event_to_complex_event_to_abjad_container_converters_converter: mutwo_abjad.NestedComplexEventToComplexEventToAbjadContainerConvertersConverter,
        complex_event_to_abjad_container_name=lambda complex_event: complex_event.tag,
        post_process_abjad_container_routines: typing.Sequence = tuple([]),
    ):
        if ADD_TIME_BRACKET_MARKS:
            post_process_abjad_container_routines = tuple(
                post_process_abjad_container_routines
            ) + (abjad_process_container_routines.AddTimeBracketMarks(),)
        super().__init__(
            nested_complex_event_to_complex_event_to_abjad_container_converters_converter,
            abjad.Score,
            "Score",
            complex_event_to_abjad_container_name,
            [],
            post_process_abjad_container_routines,
        )


# ######################################################## #
#     IslandSimultaneousEventToAbjadStaffGroupConverter    #
# ######################################################## #


class IslandSimultaneousEventToAbjadStaffGroupConverter(
    mutwo_abjad.NestedComplexEventToAbjadContainerConverter
):
    def __init__(
        self,
        post_process_abjad_container_routines: typing.Sequence = [],
        lilypond_type_of_abjad_container: str = "StaffGroup",
        mutwo_pitch_to_abjad_pitch_converter=mutwo_abjad.MutwoPitchToHEJIAbjadPitchConverter(
            reference_pitch=concert_pitch.REFERENCE.pitch_class_name
        ),
        sequential_event_to_abjad_voice_converter_class: type = mutwo_abjad.SequentialEventToAbjadVoiceConverter,
    ):
        sequential_event_to_abjad_voice_converter = sequential_event_to_abjad_voice_converter_class(
            mutwo_abjad.SequentialEventToDurationLineBasedQuantizedAbjadContainerConverter(),
            mutwo_pitch_to_abjad_pitch_converter=mutwo_pitch_to_abjad_pitch_converter,
            tempo_envelope_to_abjad_attachment_tempo_converter=None,
            write_multimeasure_rests=False,
            mutwo_volume_to_abjad_attachment_dynamic_converter=None,
        )
        super().__init__(
            mutwo_abjad.CycleBasedNestedComplexEventToComplexEventToAbjadContainerConvertersConverter(
                (sequential_event_to_abjad_voice_converter,)
            ),
            abjad.StaffGroup,
            lilypond_type_of_abjad_container,
            pre_process_abjad_container_routines=[],
            post_process_abjad_container_routines=post_process_abjad_container_routines,
        )


class IslandSaxophoneToAbjadStaffGroupConverter(
    IslandSimultaneousEventToAbjadStaffGroupConverter,
):
    def __init__(self):
        instrument_mixin = ot3_abjad_process_container_routines.SaxophoneMixin()
        self._instrument_id = instruments.ID_SAXOPHONE
        super().__init__(
            post_process_abjad_container_routines=[instrument_mixin],
        )


class IslandViolinToAbjadStaffGroupConverter(
    IslandSimultaneousEventToAbjadStaffGroupConverter,
):
    def __init__(self):
        instrument_mixin = ot3_abjad_process_container_routines.ViolinMixin()
        self._instrument_id = instruments.ID_VIOLIN
        super().__init__(
            post_process_abjad_container_routines=[instrument_mixin],
            sequential_event_to_abjad_voice_converter_class=ViolinSequentialEventToAbjadVoiceConverter,
        )


class IslandDroneToAbjadStaffGroupConverter(
    IslandSimultaneousEventToAbjadStaffGroupConverter,
):
    def __init__(self):
        super().__init__(
            post_process_abjad_container_routines=[
                ot3_abjad_process_container_routines.DroneMixin()
            ],
        )


# ######################################################## #
#         IslandTimeBracketToAbjadScoreConverter           #
# ######################################################## #

global NTH_SAX_ISLAND_COUNTER
global NTH_VIOLIN_ISLAND_COUNTER
NTH_SAX_ISLAND_COUNTER = 0
NTH_VIOLIN_ISLAND_COUNTER = 0


class IslandTimeBracketToAbjadScoreConverter(TimeBracketToAbjadScoreConverter):
    def __init__(
        self,
        nested_complex_event_to_complex_event_to_abjad_container_converters_converter: mutwo_abjad.NestedComplexEventToComplexEventToAbjadContainerConvertersConverter,
        post_process_abjad_container_routines: typing.Sequence = tuple([]),
    ):
        def get_score_name(_):
            score_name = f"islandScore{self._get_counter()}"
            self._increment_counter()
            return score_name

        post_process_abjad_container_routines = tuple(
            post_process_abjad_container_routines
        ) + (ot3_abjad_process_container_routines.PostProcessIslandTimeBracket(),)

        super().__init__(
            nested_complex_event_to_complex_event_to_abjad_container_converters_converter,
            get_score_name,
            post_process_abjad_container_routines,
        )

    @abc.abstractmethod
    def _get_counter(self):
        raise NotImplementedError

    @abc.abstractmethod
    def _increment_counter(self):
        raise NotImplementedError


class IslandSaxophoneToAbjadScoreConverter(IslandTimeBracketToAbjadScoreConverter):
    def __init__(self):
        island_instrument_to_abjad_staff_group_converter = (
            IslandSaxophoneToAbjadStaffGroupConverter()
        )
        drone_to_abjad_staff_group_converter = IslandDroneToAbjadStaffGroupConverter()
        super().__init__(
            mutwo_abjad.TagBasedNestedComplexEventToComplexEventToAbjadContainerConvertersConverter(
                {
                    island_instrument_to_abjad_staff_group_converter._instrument_id: island_instrument_to_abjad_staff_group_converter,
                    instruments.ID_DRONE: drone_to_abjad_staff_group_converter,
                }
            )
        )

    def _get_counter(self):
        return NTH_SAX_ISLAND_COUNTER

    def _increment_counter(self):
        globals()["NTH_SAX_ISLAND_COUNTER"] += 1


class IslandViolinToAbjadScoreConverter(IslandTimeBracketToAbjadScoreConverter):
    def __init__(self):
        island_instrument_to_abjad_staff_group_converter = (
            IslandViolinToAbjadStaffGroupConverter()
        )
        drone_to_abjad_staff_group_converter = IslandDroneToAbjadStaffGroupConverter()
        super().__init__(
            mutwo_abjad.TagBasedNestedComplexEventToComplexEventToAbjadContainerConvertersConverter(
                {
                    island_instrument_to_abjad_staff_group_converter._instrument_id: island_instrument_to_abjad_staff_group_converter,
                    instruments.ID_DRONE: drone_to_abjad_staff_group_converter,
                }
            )
        )

    def _get_counter(self):
        return NTH_VIOLIN_ISLAND_COUNTER

    def _increment_counter(self):
        globals()["NTH_VIOLIN_ISLAND_COUNTER"] += 1


# ######################################################## #
#   WestminsterSimultaneousEventToAbjadStaffGroupConverter #
# ######################################################## #


class WestminsterSimultaneousEventToAbjadStaffGroupConverter(
    mutwo_abjad.NestedComplexEventToAbjadContainerConverter
):
    _search_tree = nauert.UnweightedSearchTree(
        definition={
            2: {  # 1/2
                2: {2: {2: {2: None}}},  # 1/4  # 1/8  # 1/16  # 1/12
                # 5: {2: None},  # 1/10
                7: None,  # 1/14
            },
            3: {
                2: {2: {2: None}, 3: None},
                5: None,
            },  # 1/3  # 1/6  # 1/12  # 1/9  # 1/15
            5: {2: {2: {2: None}, 3: None}, 3: None},  # 1/5  # 1/10  # 1/15
            # 7: {2: {2: {2: None}}},  # 1/5  # 1/10  # 1/15
        }
    )

    def __init__(
        self,
        tempo_envelope: expenvelope.Envelope,
        time_signatures: typing.Tuple[typing.Tuple[int, int], ...],
        is_main: bool,
        post_process_abjad_container_routines: typing.Sequence = [],
        lilypond_type_of_abjad_container: str = "StaffGroup",
        mutwo_pitch_to_abjad_pitch_converter=mutwo_abjad.MutwoPitchToHEJIAbjadPitchConverter(
            reference_pitch=concert_pitch.REFERENCE.pitch_class_name
        ),
    ):
        if not is_main and not ADD_TICKS:
            post_process_abjad_container_routines = list(
                post_process_abjad_container_routines
            ) + [abjad_process_container_routines.SetStaffSize(-3)]

        sequential_event_to_abjad_voice_converter = mutwo_abjad.SequentialEventToAbjadVoiceConverter(
            mutwo_abjad.ComplexSequentialEventToQuantizedAbjadContainerConverter(
                time_signatures=tuple(
                    abjad.TimeSignature(time_signature)
                    for time_signature in time_signatures
                ),
                tempo_envelope=tempo_envelope,
                search_tree=self._search_tree,
            ),
            mutwo_pitch_to_abjad_pitch_converter=mutwo_pitch_to_abjad_pitch_converter,
            mutwo_volume_to_abjad_attachment_dynamic_converter=None,
        )
        super().__init__(
            mutwo_abjad.CycleBasedNestedComplexEventToComplexEventToAbjadContainerConvertersConverter(
                (sequential_event_to_abjad_voice_converter,)
            ),
            abjad.Staff,
            lilypond_type_of_abjad_container,
            pre_process_abjad_container_routines=[],
            post_process_abjad_container_routines=post_process_abjad_container_routines,
        )


class WestminsterSaxophoneToAbjadStaffGroupConverter(
    WestminsterSimultaneousEventToAbjadStaffGroupConverter,
):
    def __init__(
        self,
        tempo_envelope: expenvelope.Envelope,
        time_signatures: typing.Tuple[typing.Tuple[int, int], ...],
        is_main: bool = True,
    ):
        instrument_mixin = ot3_abjad_process_container_routines.SaxophoneMixin()
        self._instrument_id = instruments.ID_SAXOPHONE
        super().__init__(
            tempo_envelope,
            time_signatures,
            is_main,
            post_process_abjad_container_routines=[instrument_mixin],
        )


class WestminsterViolinToAbjadStaffGroupConverter(
    WestminsterSimultaneousEventToAbjadStaffGroupConverter,
):
    def __init__(
        self,
        tempo_envelope: expenvelope.Envelope,
        time_signatures: typing.Tuple[typing.Tuple[int, int], ...],
        is_main: bool = True,
    ):
        instrument_mixin = ot3_abjad_process_container_routines.ViolinMixin()
        self._instrument_id = instruments.ID_VIOLIN
        super().__init__(
            tempo_envelope,
            time_signatures,
            is_main,
            post_process_abjad_container_routines=[instrument_mixin],
        )


# ######################################################## #
#         WestminsterBracketToAbjadScoreConverter          #
# ######################################################## #


class WestminsterTimeBracketToAbjadScoreConverter(TimeBracketToAbjadScoreConverter):
    _nth_westminster_counter = 0

    def __init__(
        self,
        tempo: float,
        time_signatures: typing.Tuple[typing.Tuple[int, int], ...],
        main_instrument: str = "violin",
        post_process_abjad_container_routines: typing.Sequence = tuple([]),
    ):
        def get_score_name(_):
            score_name = f"westminsterScore{self._get_counter()}"
            self._increment_counter()
            return score_name

        tempo_envelope = expenvelope.Envelope.from_points((0, tempo), (1, tempo))
        instrument_to_abjad_staff_group_converter0 = (
            WestminsterViolinToAbjadStaffGroupConverter(
                tempo_envelope, time_signatures, main_instrument == "violin"
            )
        )
        instrument_to_abjad_staff_group_converter1 = (
            WestminsterSaxophoneToAbjadStaffGroupConverter(
                tempo_envelope, time_signatures, main_instrument != "violin"
            )
        )
        post_process_abjad_container_routines = tuple(
            post_process_abjad_container_routines
        ) + (ot3_abjad_process_container_routines.PostProcessWestminsterTimeBracket(ADD_TICKS),)

        super().__init__(
            mutwo_abjad.TagBasedNestedComplexEventToComplexEventToAbjadContainerConvertersConverter(
                {
                    instrument_to_abjad_staff_group_converter0._instrument_id: instrument_to_abjad_staff_group_converter0,
                    instrument_to_abjad_staff_group_converter1._instrument_id: instrument_to_abjad_staff_group_converter1,
                }
            ),
            get_score_name,
            post_process_abjad_container_routines,
        )

    def convert(self, time_bracket_to_convert) -> abjad.Score:
        score = super().convert(time_bracket_to_convert)
        if ADD_TICKS:
            note_length = 4
            n_notes = int(time_bracket_to_convert[0].duration * note_length)
            staff = abjad.Staff(
                [abjad.Voice([abjad.Note(f"b'{note_length}") for _ in range(n_notes)])]
            )
            ot3_abjad_process_container_routines.TicksMixin()(None, staff)
            # abjad_process_container_routines.SetStaffSize(-1)(None, staff)
            score.append(staff)

        return score


global NTH_SAX_WESTMINSTER_COUNTER
global NTH_VIOLIN_WESTMINSTER_COUNTER
NTH_SAX_WESTMINSTER_COUNTER = 0
NTH_VIOLIN_WESTMINSTER_COUNTER = 0


class WestminsterViolinToAbjadScoreConverter(
    WestminsterTimeBracketToAbjadScoreConverter
):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, main_instrument="violin", **kwargs)

    def _get_counter(self):
        return NTH_VIOLIN_WESTMINSTER_COUNTER

    def _increment_counter(self):
        globals()["NTH_VIOLIN_WESTMINSTER_COUNTER"] += 1


class WestminsterSaxophoneToAbjadScoreConverter(
    WestminsterTimeBracketToAbjadScoreConverter
):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, main_instrument="saxophone", **kwargs)

    def _get_counter(self):
        return NTH_SAX_WESTMINSTER_COUNTER

    def _increment_counter(self):
        globals()["NTH_SAX_WESTMINSTER_COUNTER"] += 1


# ######################################################## #
#            AbjadScoresToLilypondFileConverter            #
# ######################################################## #


class AbjadScoresToLilypondFileConverter(converters_abc.Converter):
    def __init__(
        self,
        instrument: typing.Optional[str] = None,
        paper_format: ot3_abjad_constants.PaperFormat = ot3_abjad_constants.A4,
        margin: float = 4,
        add_header_block: bool = True,
        add_paper_block: bool = True,
        add_layout_block: bool = True,
    ):
        self._instrument = instrument
        self._paper_format = paper_format
        self._margin = margin
        self._add_header_block = add_header_block
        self._add_paper_block = add_paper_block
        self._add_layout_block = add_layout_block

    def _stress_instrument(self, abjad_score: abjad.Score):
        pass

    @staticmethod
    def _make_header_block(instrument: typing.Optional[str]) -> abjad.Block:
        header_block = abjad.Block("header")
        header_block.title = '"ohne Titel (3)"'
        header_block.dedication = '"dedicated to Philipp Diederich & Mariana Hernández"'
        header_block.year = '"2021"'
        header_block.composer = '"Levin Eric Zimmermann"'
        header_block.tagline = '"oT(3) // 2021"'
        if instrument:
            header_block.instrument = instruments.INSTRUMENT_ID_TO_LONG_INSTRUMENT_NAME[
                instrument
            ]
        return header_block

    @staticmethod
    def _make_paper_block() -> abjad.Block:
        paper_block = abjad.Block("paper")
        paper_block.items.append(
            r"""#(define fonts
    (make-pango-font-tree "EB Garamond"
                          "Nimbus Sans"
                          "Luxi Mono"
                          (/ staff-height pt 20)))"""
        )
        paper_block.items.append(
            r"""score-system-spacing =
      #'((basic-distance . 30)
       (minimum-distance . 18)
       (padding . 2.5)
       (stretchability . 12))"""
        )
        return paper_block

    @staticmethod
    def _make_layout_block(margin: int) -> abjad.Block:
        layout_block = abjad.Block("layout")
        layout_block.items.append(r"short-indent = {}\mm".format(margin))
        layout_block.items.append(r"ragged-last = ##f")
        layout_block.items.append(r"indent = {}\mm".format(margin))
        return layout_block

    def convert(self, abjad_scores: typing.Sequence[abjad.Score]) -> abjad.LilyPondFile:
        lilypond_file = abjad.LilyPondFile(
            includes=["ekme-heji-ref-c-not-tuned.ily", "fancy-glissando.ly"],
            default_paper_size=self._paper_format.name,
        )

        layout_block = AbjadScoresToLilypondFileConverter._make_layout_block(
            self._margin
        )
        for abjad_score in abjad_scores:
            score_block = abjad.Block("score")
            score_block.items.append(abjad_score)
            if self._add_layout_block:
                score_block.items.append(layout_block)
            lilypond_file.items.append(score_block)

        if self._add_header_block:
            lilypond_file.items.append(
                AbjadScoresToLilypondFileConverter._make_header_block(self._instrument)
            )
        # lilypond_file.items.append(
        #     AbjadScoresToLilypondFileConverter._make_layout_block(self._margin)
        # )
        if self._add_paper_block:
            lilypond_file.items.append(
                AbjadScoresToLilypondFileConverter._make_paper_block()
            )

        lilypond_file.items.append("\\pointAndClickOff\n")

        return lilypond_file
