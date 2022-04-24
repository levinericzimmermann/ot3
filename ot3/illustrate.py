import typing

import abjad

from mutwo import converters
from mutwo import events
from mutwo import parameters
from mutwo import utilities

from ot3 import constants as ot3_constants
from ot3 import parameters as ot3_parameters


class AddCadenza(
    converters.frontends.abjad_process_container_routines.ProcessAbjadContainerRoutine
):
    def __call__(
        self, _, container_to_process: abjad.Container,
    ):
        first_leaf = abjad.get.leaf(container_to_process[0], 0)
        abjad.attach(
            abjad.LilyPondLiteral("\\cadenzaOn"), first_leaf,
        )
        abjad.attach(
            abjad.LilyPondLiteral("\\omit Staff.TimeSignature"), first_leaf,
        )


ILLUSTRATE_PATH = "builds/illustrations"


def _make_standard_sequential_converter():
    return converters.frontends.abjad.SequentialEventToAbjadVoiceConverter(
        mutwo_pitch_to_abjad_pitch_converter=converters.frontends.abjad.MutwoPitchToHEJIAbjadPitchConverter(
            ot3_constants.concert_pitch.REFERENCE.pitch_class_name
        ),
        tempo_envelope_to_abjad_attachment_tempo_converter=None,
        mutwo_volume_to_abjad_attachment_dynamic_converter=None,
    )


def _make_standard_score_converter(
    sequential_event_to_abjad_voice_converter=_make_standard_sequential_converter(),
    post_process_abjad_container_routines=[],
):
    return converters.frontends.abjad.NestedComplexEventToAbjadContainerConverter(
        converters.frontends.abjad.CycleBasedNestedComplexEventToComplexEventToAbjadContainerConvertersConverter(
            (sequential_event_to_abjad_voice_converter,)
        ),
        abjad.Score,
        "Score",
        pre_process_abjad_container_routines=[],
        post_process_abjad_container_routines=[
            converters.frontends.abjad_process_container_routines.AddAccidentalStyle(
                "dodecaphonic"
            )
        ]
        + post_process_abjad_container_routines,
    )


def illustrate(
    name: str,
    *abjad_score: abjad.Score,
    add_book_preamble: bool = True,
    add_ekmeheji: bool = True,
):

    margin = 0
    layout_block = abjad.Block("layout")
    layout_block.items.append(r"short-indent = {}\mm".format(margin))
    layout_block.items.append(r"ragged-last = ##f")
    layout_block.items.append(r"indent = {}\mm".format(margin))
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
       (padding . 1)
       (stretchability . 12))"""
    )
    includes = []
    if add_ekmeheji:
        includes.append("ekme-heji-ref-c.ily")
    if add_book_preamble:
        includes.append("lilypond-book-preamble.ly")
    lilypond_file = abjad.LilyPondFile(
        items=list(abjad_score) + [paper_block, layout_block], includes=includes,
    )
    abjad.persist.as_pdf(lilypond_file, f"{ILLUSTRATE_PATH}/{name}.pdf")


def illustrate_scordatura(
    original_tuning: typing.Sequence[parameters.pitches.JustIntonationPitch],
    scordatura: typing.Sequence[parameters.pitches.JustIntonationPitch],
):
    sequential_event = events.basic.SequentialEvent(
        [events.music.NoteLike(pitch, 1) for pitch in scordatura]
    )
    for event, original_pitch in zip(sequential_event, original_tuning):
        pitch_to_process = event.pitch_or_pitches[0]
        difference = (pitch_to_process - original_pitch).cents
        event.notation_indicators.cent_deviation.deviation = difference

    score_converter = _make_standard_score_converter(
        post_process_abjad_container_routines=[
            AddCadenza(),
            converters.frontends.abjad_process_container_routines.AddInstrumentName(
                lambda _: "vl scordatura", lambda _: ""
            ),
        ]
    )
    score = score_converter.convert(events.basic.SimultaneousEvent([sequential_event]))
    illustrate("violin_scordatura", score)


def illustrate_harmonics(
    tuning: typing.Sequence[parameters.pitches.JustIntonationPitch],
    harmonics_per_string: typing.Sequence[
        typing.Sequence[parameters.pitches.JustIntonationPitch]
    ],
):
    score_converter = _make_standard_score_converter(
        post_process_abjad_container_routines=[
            AddCadenza(),
            converters.frontends.abjad_process_container_routines.AddInstrumentName(
                lambda _: "vl scordatura", lambda _: ""
            ),
        ]
    )
    scores = []
    for string_pitch, harmonics in zip(tuning, harmonics_per_string):
        sequential_event = events.basic.SequentialEvent([])
        for pitch in [string_pitch] + list(harmonics):
            note = events.music.NoteLike(pitch, 1)
            note.notation_indicators.markup.content = f"{pitch.ratio}"
            note.notation_indicators.markup.direction = "up"
            sequential_event.append(note)
        score = score_converter.convert(
            events.basic.SimultaneousEvent([sequential_event])
        )
        scores.append(score)

    # show all pitches in rising order
    concatenated_pitches = list(tuning)
    for harmonics in harmonics_per_string:
        for pitch in harmonics:
            concatenated_pitches.append(pitch)

    sorted_uniqified_pitches = sorted(
        utilities.tools.uniqify_iterable(concatenated_pitches)
    )
    sequential_event = events.basic.SequentialEvent(
        [events.music.NoteLike(pitch, 1) for pitch in sorted_uniqified_pitches]
    )
    for note in sequential_event:
        note.notation_indicators.markup.content = f"{note.pitch_or_pitches[0].ratio}"
        note.notation_indicators.markup.direction = "up"

    print(f"Violin has {len(sequential_event)} different harmonic pitches")

    score = score_converter.convert(events.basic.SimultaneousEvent([sequential_event]))
    scores.append(score)

    # show all pitch classes
    sorted_pitch_classes = sorted(
        utilities.tools.uniqify_iterable(
            tuple(p.normalize(mutate=False) for p in sorted_uniqified_pitches)
        )
    )
    sequential_event = events.basic.SequentialEvent(
        [events.music.NoteLike(pitch, 1) for pitch in sorted_pitch_classes]
    )

    for note in sequential_event:
        note.notation_indicators.markup.content = f"{note.pitch_or_pitches[0].ratio}"
        note.notation_indicators.markup.direction = "up"

    print(f"Violin has {len(sequential_event)} different pitch classes")

    score = score_converter.convert(events.basic.SimultaneousEvent([sequential_event]))
    scores.append(score)

    illustrate("violin_flageolets", *scores)


def illustrate_available_pitches(
    notateable_pitch_to_pitch_counter: typing.Dict[typing.Tuple[int, ...], int]
):

    score_converter = _make_standard_score_converter()
    available_pitches = []
    for pitch_as_exponent in notateable_pitch_to_pitch_counter.keys():
        available_pitches.append(
            (
                parameters.pitches.JustIntonationPitch(pitch_as_exponent),
                pitch_as_exponent,
            )
        )

    sorted_available_pitches = sorted(available_pitches, key=lambda pair: pair[0])

    sequential_event = events.basic.SequentialEvent([])
    for pitch, pitch_as_exponent in sorted_available_pitches:
        note = events.music.NoteLike(pitch, 1)
        note.notation_indicators.markup.content = (
            f"{note.pitch_or_pitches[0].ratio},"
            f" {notateable_pitch_to_pitch_counter[pitch_as_exponent]}"
        )
        note.notation_indicators.markup.direction = "up"
        sequential_event.append(note)

    print(f"oT(3) has {len(sequential_event)} different pitches")

    score = score_converter.convert(events.basic.SimultaneousEvent([sequential_event]))
    illustrate("all_pitches", score, add_book_preamble=False)


def illustrate_available_pitches_with_focus_on_deviation(
    notateable_pitch_to_pitch_counter: typing.Dict[typing.Tuple[int, ...], int]
):

    min_amount = 4

    score_converter = _make_standard_score_converter()
    available_pitches = []
    for pitch_as_exponent, n_times in notateable_pitch_to_pitch_counter.items():
        if n_times > min_amount:
            available_pitches.append(
                (
                    parameters.pitches.JustIntonationPitch(pitch_as_exponent),
                    pitch_as_exponent,
                )
            )

    sorted_available_pitches = sorted(available_pitches, key=lambda pair: pair[0])

    sequential_event = events.basic.SequentialEvent([])
    for pitch, pitch_as_exponent in sorted_available_pitches:
        note = events.music.NoteLike(pitch, 1)
        note.notation_indicators.markup.content = (
            f"{note.pitch_or_pitches[0].ratio},"
            f" {round(pitch.cent_deviation_from_closest_western_pitch_class, 2)}"
        )
        note.notation_indicators.markup.direction = "up"
        sequential_event.append(note)

    score = score_converter.convert(events.basic.SimultaneousEvent([sequential_event]))
    illustrate("most_pitches", score, add_book_preamble=False)


def illustrate_pitch_set_based_ambitus(
    pitch_set_based_ambitus: ot3_parameters.ambitus.SetBasedAmbitus, name: str
):

    score_converter = _make_standard_score_converter()

    sequential_event = events.basic.SequentialEvent([])
    for pitch in pitch_set_based_ambitus.pitches:
        note = events.music.NoteLike(pitch, 1)
        note.notation_indicators.markup.content = f"{note.pitch_or_pitches[0].ratio}"
        note.notation_indicators.markup.direction = "up"
        deviation = pitch.cent_deviation_from_closest_western_pitch_class
        note.notation_indicators.cent_deviation.deviation = deviation
        sequential_event.append(note)

    score = score_converter.convert(events.basic.SimultaneousEvent([sequential_event]))
    illustrate(name, score, add_book_preamble=False)


def illustrate_saxophone_multiphonics():
    score_converter = _make_standard_score_converter()

    sequential_event = events.basic.SequentialEvent([])
    for (
        name,
        dynamics,
        western_pitches_with_deviation,
        multiphonic_fingering,
    ) in (
        ot3_constants.instruments.SAXOPHONE_MULTIPHONIC_PITCHES_TO_MULTIPHONICS_DATA.values()
    ):
        western_pitches, deviations = zip(*western_pitches_with_deviation)
        western_pitches = tuple(western_pitches)
        for pitch, deviation in zip(western_pitches, deviations):
            if deviation == 50:
                pitch.pitch_class_name = f"{pitch.pitch_class_name}qs"
            elif deviation == -50:
                pitch.pitch_class_name = f"{pitch.pitch_class_name}qf"
        note = events.music.NoteLike(western_pitches, 1)
        (
            note.playing_indicators.fingering.cc,
            note.playing_indicators.fingering.rh,
            note.playing_indicators.fingering.lh,
        ) = (
            tuple(multiphonic_fingering.cc),
            tuple(multiphonic_fingering.rh),
            tuple(multiphonic_fingering.lh),
        )
        note.notation_indicators.markup.content = f"{name}, Dynamics: {dynamics}"
        note.notation_indicators.markup.direction = "up"
        sequential_event.append(note)

    """
    note = events.music.NoteLike(
        [
            parameters.pitches.WesternPitch("cs", 5),
            parameters.pitches.WesternPitch("eqf", 5),
        ],
        1,
    )
    (
        note.playing_indicators.fingering.cc,
        note.playing_indicators.fingering.lh,
        note.playing_indicators.fingering.rh,
    ) = (
        ("one", "two", "three", "four", "six"),
        ("front-f",),
        ("low-c",),
    )

    note.notation_indicators.markup.content = (
        "weiss 112 (alternative for kientzy 65), Dynamics: (pp,)"
    )
    note.notation_indicators.markup.direction = "up"

    sequential_event.insert(4, note)
    """

    score = score_converter.convert(events.basic.SimultaneousEvent([sequential_event]))
    abjad.attach(
        abjad.LilyPondLiteral("\\override Score.SpacingSpanner spacing-increment = 25"),
        abjad.get.leaf(score, 0),
    )
    abjad.attach(
        abjad.LilyPondLiteral("\\omit Staff.BarLine"), abjad.get.leaf(score, 0),
    )
    abjad.attach(
        abjad.LilyPondLiteral("\\omit Staff.TimeSignature"), abjad.get.leaf(score, 0),
    )
    illustrate(
        "saxophone_multiphonics", score, add_book_preamble=True, add_ekmeheji=False
    )


def illustrate_saxophone_microtonal_pitches():
    score_converter = _make_standard_score_converter()

    sequential_event = events.basic.SequentialEvent([])
    for (
        microtonal_pitch_as_exponents
    ) in (
        ot3_constants.instruments.SAXOPHONE_MICROTONAL_PITCHES_TO_COMBINED_FINGERINGS.keys()
    ):
        note = events.music.NoteLike(
            [parameters.pitches.JustIntonationPitch(microtonal_pitch_as_exponents)], 1
        )
        ot3_constants.instruments.apply_saxophone_pitch(note)
        sequential_event.append(note)

    score = score_converter.convert(events.basic.SimultaneousEvent([sequential_event]))
    abjad.attach(
        abjad.LilyPondLiteral("\\override Score.SpacingSpanner spacing-increment = 8"),
        abjad.get.leaf(score, 0),
    )
    abjad.attach(
        abjad.LilyPondLiteral("\\omit Staff.BarLine"), abjad.get.leaf(score, 0),
    )
    abjad.attach(
        abjad.LilyPondLiteral("\\omit Staff.TimeSignature"), abjad.get.leaf(score, 0),
    )
    illustrate(
        "saxophone_microtonal_pitches",
        score,
        add_book_preamble=True,
        add_ekmeheji=False,
    )


def illustrate_saxophone_ambitus_in_transposed_notation():
    score_converter = _make_standard_score_converter()

    sequential_event = events.basic.SequentialEvent([])
    for (
        pitch_as_exponents,
        pitch_data,
    ) in (
        ot3_constants.instruments.SOUNDING_SAXOPHONE_PITCH_TO_WRITTEN_SAXOPHONE_PITCH_AND_CENT_DEVIATION.items()
    ):
        pitch_as_western_pitch, cent_deviation = pitch_data
        note = events.music.NoteLike(pitch_as_western_pitch, 1)
        note.notation_indicators.cent_deviation.deviation = cent_deviation
        note.notation_indicators.markup.content = (
            f"{parameters.pitches.JustIntonationPitch(pitch_as_exponents).ratio}"
        )
        note.notation_indicators.markup.direction = "up"
        sequential_event.append(note)

    score = score_converter.convert(events.basic.SimultaneousEvent([sequential_event]))
    illustrate("saxophone_pitches_transposed", score, add_book_preamble=False)


def main():
    illustrate_saxophone_microtonal_pitches()
    illustrate_saxophone_multiphonics()
    illustrate_saxophone_ambitus_in_transposed_notation()
    illustrate_pitch_set_based_ambitus(
        ot3_constants.instruments.AMBITUS_SAXOPHONE_JUST_INTONATION_PITCHES,
        "saxophone_pitches",
    )
    illustrate_available_pitches_with_focus_on_deviation(
        ot3_constants.families_pitch.NOTATEABLE_PITCH_TO_PITCH_COUNTER
    )

    illustrate_harmonics(
        ot3_constants.instruments.SCORDATURA_VIOLIN_TUNING,
        tuple(
            string.harmonic_pitches
            for string in ot3_constants.instruments.VIOLIN.strings
        ),
    )

    illustrate_available_pitches(
        ot3_constants.families_pitch.NOTATEABLE_PITCH_TO_PITCH_COUNTER
    )

    illustrate_scordatura(
        ot3_constants.instruments.ORIGINAL_VIOLIN_TUNING,
        ot3_constants.instruments.SCORDATURA_VIOLIN_TUNING,
    )
