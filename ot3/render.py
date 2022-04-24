"""Script for exporting musical data to scores & sound files

Public interaction via "main" method.
"""


import abjad

from mutwo.converters.frontends import abjad_video_constants
from mutwo.converters.frontends import abjad_video
from mutwo.converters.symmetrical import time_brackets
from mutwo.converters.symmetrical.playing_indicators import PlayingIndicatorsConverter
from mutwo.events import basic
from mutwo.events import time_brackets as events_time_brackets
from mutwo import utilities

from ot3.constants import compute
from ot3.constants import clouds
from ot3.constants import instruments
from ot3.constants import families_pitch
from ot3.constants import time_brackets_container
from ot3.converters.frontends import abjad_attachments as ot3_abjad_attachments
from ot3.converters.frontends import abjad as ot3_abjad
from ot3.converters.frontends import csound as ot3_csound
from ot3.converters.frontends import midi as ot3_midi
from ot3.converters.symmetrical import bells
from ot3.converters.symmetrical import drones
from ot3.converters.symmetrical import playing_indicators
from ot3.converters.symmetrical import shadows
from ot3 import parameters as ot3_parameters


def _change_horizontal_spacing(leaf, make_moment_duration):
    abjad.attach(
        abjad.LilyPondLiteral(
            "\\set Score.proportionalNotationDuration = #(ly:make-moment"
            " 1/{})".format(make_moment_duration)
        ),
        leaf,
    )
    abjad.attach(
        abjad.LilyPondLiteral("\\override Staff.TimeSignature.style = #'single-digit"),
        leaf,
    )
    abjad.attach(
        abjad.LilyPondLiteral(
            "\\override SpacingSpanner.base-shortest-duration = #(ly:make-moment 1/{})".format(
                make_moment_duration
            )
        ),
        leaf,
    )


def _add_left_hand_pizz(serenade2):
    played_note = serenade2[0][0][0][3]
    copied_note = abjad.mutate.copy(played_note)
    # set microtonal pitch
    copied_note.note_head._written_pitch = played_note.note_head._written_pitch
    abjad.attach(abjad.LilyPondLiteral(r"\voiceTwo", "opening"), copied_note)
    new_voice = abjad.Voice([copied_note])
    second_voice = abjad.Voice(
        r"\voiceOne \stemUp r8 e''8 ^\markup {\teeny { (left hand pizz.) } }"
        r" \stemNeutral"
    )
    short_polyphony = abjad.Container([new_voice, second_voice], simultaneous=True)
    serenade2[0][0][0][3] = short_polyphony


def _render_soundfile_for_instrument(
    instrument_id,
    filtered_time_brackets,
    midi_file_converter,
    return_pitch: bool = False,
):
    if compute.RENDER_MIDIFILES:
        playing_indicators_converter = PlayingIndicatorsConverter(
            [
                playing_indicators.HarmonicGlissandoConverter(),
                playing_indicators.BowNoiseConverter(),
                playing_indicators.TeethOnReedConverter(),
            ]
        )
        time_brackets_converter = time_brackets.TimeBracketsToEventConverter(
            instrument_id
        )
        converted_time_brackets = time_brackets_converter.convert(
            filtered_time_brackets
        )
        if converted_time_brackets:
            if instrument_id == instruments.ID_VIOLIN:
                converted_time_brackets = tuple(
                    simev if isinstance(simev, basic.TaggedSimpleEvent) else simev[:1]
                    for simev in converted_time_brackets
                )

            n_sequential_events = max(
                len(simultaneous_event)
                for simultaneous_event in converted_time_brackets
                if isinstance(simultaneous_event, basic.SimultaneousEvent)
            )
            simultaneous_event = basic.SimultaneousEvent(
                [basic.SequentialEvent([]) for _ in range(n_sequential_events)]
            )
            for event in converted_time_brackets:
                if isinstance(event, basic.SimpleEvent):
                    rest = basic.SimpleEvent(event.duration)
                    for seq in simultaneous_event:
                        seq.append(rest)
                else:
                    for ev, sequential_event in zip(event, simultaneous_event):
                        ev = playing_indicators_converter.convert(ev)
                        for subseqev in ev:
                            sequential_event.extend(subseqev)

            if return_pitch:
                simultaneous_event.set_parameter("return_pitch", True)

            midi_file_converter.convert(simultaneous_event)


def _render_notation_for_instrument(
    filtered_time_brackets,
    time_bracket_to_score_converter,
    instrument,
    post_process_abjad_scores=lambda abjad_scores: None,
):
    if compute.RENDER_NOTATION:
        abjad_scores = []
        for time_bracket in filtered_time_brackets:
            abjad_score = time_bracket_to_score_converter(time_bracket).convert(
                time_bracket
            )
            abjad_scores.append(abjad_score)

        post_process_abjad_scores(abjad_scores)
        lilypond_file_converter = ot3_abjad.AbjadScoresToLilypondFileConverter()
        lilypond_file = lilypond_file_converter.convert(abjad_scores)
        abjad.persist.as_pdf(lilypond_file, f"builds/notations/oT3_{instrument}.pdf")


def _render_video_for_instrument(
    filtered_time_brackets,
    time_bracket_to_score_converter,
    instrument,
    post_process_abjad_scores=lambda abjad_scores: None,
):
    abjad_video_constants.DEFAULT_RESOLUTION = 230
    abjad_video_constants.DEFAULT_ADDED_X_MARGIN_FOR_COUNT_DOWN = 295
    abjad_video_constants.DEFAULT_FRAME_IMAGE_ENCODING_FOR_FREE_TIME_BRACKET = "PNG"
    abjad_video_constants.DEFAULT_FRAME_IMAGE_WRITE_KWARGS_FOR_FREE_TIME_BRACKET = {}
    if compute.RENDER_VIDEOS:
        abjad_scores = []
        for time_bracket in filtered_time_brackets:
            abjad_score = time_bracket_to_score_converter(time_bracket).convert(
                time_bracket
            )
            abjad_scores.append(abjad_score)

        post_process_abjad_scores(abjad_scores)

        lilypond_file_converter = ot3_abjad.AbjadScoresToLilypondFileConverter(
            add_paper_block=False, add_header_block=False, add_layout_block=False
        )
        lilypond_files = tuple(
            lilypond_file_converter.convert((abjad_score,))
            for abjad_score in abjad_scores
        )
        video_converter = abjad_video.TimeBracketLilypondFilesToVideoConverter()
        video_converter.convert(
            f"builds/notations/oT3_{instrument}_video_score",
            filtered_time_brackets,
            lilypond_files,
        )


def _render_saxophone():
    instrument_id = instruments.ID_SAXOPHONE
    filtered_time_brackets = time_brackets_container.TIME_BRACKETS.filter(instrument_id)

    _render_soundfile_for_instrument(
        instrument_id,
        filtered_time_brackets,
        ot3_midi.OT3InstrumentSimulationEventToMidiFileConverter("saxophone"),
        return_pitch=True,
    )

    # adjust pitch notation (add transpostion)

    for time_bracket in filtered_time_brackets:
        for tagged_simultaneous_event in time_bracket:
            if tagged_simultaneous_event.tag == instrument_id:
                for sequential_event in tagged_simultaneous_event:
                    for simple_event in sequential_event:
                        instruments.apply_saxophone_pitch(simple_event)

    # exception: the particular melodic line here makes the following
    # fingering easier (unlike all other parts)
    filtered_time_brackets[-1][1][0][
        20
    ].playing_indicators.combined_fingerings.fingerings = (
        ot3_parameters.playing_indicators.Fingering(
            cc="one two".split(" "),
            lh=("f",),
            rh=tuple([]),
        ),
    )

    def post_process_abjad_scores(abjad_scores):
        serenade0_score_index = list(map(lambda score: score.name, abjad_scores)).index(
            "westminsterScore3"
        )
        serenade0 = abjad_scores[serenade0_score_index]
        serenade0[0][0][0][-1] = abjad.Rest(1)

        # avoid fingering collision in video
        if not ot3_abjad.ADD_TIME_BRACKET_MARKS:
            _change_horizontal_spacing(serenade0[1][0][4][0], 32)
            _change_horizontal_spacing(serenade0[1][0][4][-1], 8)

        almost_last_westminster_melody_index = list(
            map(lambda score: score.name, abjad_scores)
        ).index("westminsterScore6")
        almost_last_westminster_melody = abjad_scores[
            almost_last_westminster_melody_index
        ]
        # remove rests
        del almost_last_westminster_melody[0][0][-1][-1]
        del almost_last_westminster_melody[0][0][-1][-1]
        # change time signature
        abjad.attach(
            abjad.TimeSignature((2, 2)), almost_last_westminster_melody[0][0][-1][0]
        )

        serenade2_score_index = list(map(lambda score: score.name, abjad_scores)).index(
            "westminsterScore7"
        )
        serenade2 = abjad_scores[serenade2_score_index]
        _add_left_hand_pizz(serenade2)

        third_westminster_score_index = list(
            map(lambda score: score.name, abjad_scores)
        ).index("westminsterScore2")
        third_westminster_score = abjad_scores[third_westminster_score_index]
        abjad.attach(abjad.TimeSignature((2, 2)), third_westminster_score[0][0][-1][0])

    def time_bracket_to_abjad_score_converter_for_video(time_bracket):
        if isinstance(time_bracket, events_time_brackets.TempoBasedTimeBracket):
            ot3_abjad_attachments.Fingering.fingering_size = 0.65
            return ot3_abjad.WestminsterSaxophoneToAbjadScoreConverter(
                time_bracket.tempo,
                (
                    lambda: time_bracket.time_signatures
                    if hasattr(time_bracket, "time_signatures")
                    else ((5, 2),)
                )(),
            )
        else:
            ot3_abjad_attachments.Fingering.fingering_size = 0.7
            return ot3_abjad.IslandSaxophoneToAbjadScoreConverter()

    def time_bracket_to_abjad_score_converter_for_notation(time_bracket):
        if isinstance(time_bracket, events_time_brackets.TempoBasedTimeBracket):
            return ot3_abjad.WestminsterSaxophoneToAbjadScoreConverter(
                time_bracket.tempo,
                (
                    lambda: time_bracket.time_signatures
                    if hasattr(time_bracket, "time_signatures")
                    else ((5, 2),)
                )(),
            )
        else:
            return ot3_abjad.IslandSaxophoneToAbjadScoreConverter()

    ot3_abjad.ADD_TIME_BRACKET_MARKS = False
    ot3_abjad.ADD_TICKS = True
    _render_video_for_instrument(
        filtered_time_brackets,
        time_bracket_to_abjad_score_converter_for_video,
        instrument_id,
        post_process_abjad_scores=post_process_abjad_scores,
    )

    ot3_abjad.ADD_TIME_BRACKET_MARKS = True
    ot3_abjad.ADD_TICKS = False
    ot3_abjad_attachments.Fingering.fingering_size = 0.7
    _render_notation_for_instrument(
        filtered_time_brackets,
        time_bracket_to_abjad_score_converter_for_notation,
        instrument_id,
        post_process_abjad_scores=post_process_abjad_scores,
    )


def _render_violin():
    instrument_id = instruments.ID_VIOLIN
    filtered_time_brackets = time_brackets_container.TIME_BRACKETS.filter(instrument_id)

    _render_soundfile_for_instrument(
        instrument_id,
        filtered_time_brackets,
        ot3_midi.OT3InstrumentSimulationEventToMidiFileConverter("violin"),
        return_pitch=True,
    )

    def post_process_abjad_scores(abjad_scores):
        serenade0_score_index = list(map(lambda score: score.name, abjad_scores)).index(
            "westminsterScore0"
        )
        serenade0 = abjad_scores[serenade0_score_index]

        serenade0 = abjad_scores[serenade0_score_index]
        serenade0[0][0][0][-1] = abjad.Rest(1)

        serenade2_score_index = list(map(lambda score: score.name, abjad_scores)).index(
            "westminsterScore2"
        )
        serenade2 = abjad_scores[serenade2_score_index]
        _add_left_hand_pizz(serenade2)

    def time_bracket_to_abjad_score_converter(time_bracket):
        if isinstance(time_bracket, events_time_brackets.TempoBasedTimeBracket):
            return ot3_abjad.WestminsterViolinToAbjadScoreConverter(
                time_bracket.tempo,
                (
                    lambda: time_bracket.time_signatures
                    if hasattr(time_bracket, "time_signatures")
                    else ((5, 2),)
                )(),
            )
        else:
            return ot3_abjad.IslandViolinToAbjadScoreConverter()

    ot3_abjad.ADD_TIME_BRACKET_MARKS = False
    ot3_abjad.ADD_TICKS = True
    _render_video_for_instrument(
        filtered_time_brackets,
        time_bracket_to_abjad_score_converter,
        instrument_id,
        post_process_abjad_scores=post_process_abjad_scores,
    )

    ot3_abjad.ADD_TIME_BRACKET_MARKS = True
    ot3_abjad.ADD_TICKS = False
    _render_notation_for_instrument(
        filtered_time_brackets,
        time_bracket_to_abjad_score_converter,
        instrument_id,
        post_process_abjad_scores=post_process_abjad_scores,
    )


def _render_drone():
    if compute.RENDER_MIDIFILES:
        families_pitch_to_drones_converter = drones.FamiliesPitchToDronesConverter()
        loudspeaker_to_simultaneous_event = families_pitch_to_drones_converter.convert(
            families_pitch.FAMILIES_PITCH
        )
        for (
            loudspeaker,
            simultaneous_event,
        ) in loudspeaker_to_simultaneous_event.items():
            for nth_sequential_event, sequential_event in enumerate(simultaneous_event):
                converter = ot3_midi.OT3InstrumentEventToMidiFileConverter(
                    f"drone_{loudspeaker}_{nth_sequential_event}"
                )
                converter.convert(sequential_event)


def _render_bells():
    @utilities.decorators.compute_lazy(
        "ot3/constants/.bells.pickle", force_to_compute=compute.COMPUTE_BELLS
    )
    def _make_bell_sequential_events(n_bells):
        bell_events = []
        for nth_bell in range(n_bells):
            family_of_pitch_curves_to_bell_converter = (
                bells.FamilyOfPitchCurvesToBellConverter(seed=nth_bell)
            )
            sequential_event = family_of_pitch_curves_to_bell_converter.convert(
                families_pitch.FAMILY_PITCH
            )
            bell_events.append(sequential_event)
        return tuple(bell_events)

    if compute.RENDER_MIDIFILES:
        bell_events = _make_bell_sequential_events(clouds.N_BELLS)
        for nth_bell, sequential_event in enumerate(bell_events):
            midi_file_converter = ot3_midi.OT3InstrumentEventToMidiFileConverter(
                f"bell{nth_bell}", min_velocity=1, max_velocity=100, apply_extrema=True
            )
            midi_file_converter.convert(sequential_event)


def _render_sine(instrument_id):
    filtered_time_brackets = time_brackets_container.TIME_BRACKETS.filter(instrument_id)

    _render_soundfile_for_instrument(
        instrument_id,
        filtered_time_brackets,
        ot3_csound.SineTonesToSoundFileConverter(instrument_id),
    )


def _render_sines():
    if compute.RENDER_SOUNDFILES:
        for instrument_ids in instruments.ID_INSTR_TO_ID_SINES.values():
            for instrument_id in instrument_ids:
                _render_sine(instrument_id)


def _render_mode(instrument_id):
    filtered_time_brackets = time_brackets_container.TIME_BRACKETS.filter(instrument_id)

    _render_soundfile_for_instrument(
        instrument_id,
        filtered_time_brackets,
        ot3_midi.OT3InstrumentEventToMidiFileConverter(
            instrument_id, apply_extrema=True, min_velocity=30, max_velocity=100
        ),
    )


def _render_modes():
    if compute.RENDER_MIDIFILES:
        for instrument_id in instruments.MODE_IDS:
            _render_mode(instrument_id)


def _render_saturation_sine(instrument_id):
    filtered_time_brackets = time_brackets_container.TIME_BRACKETS.filter(instrument_id)

    _render_soundfile_for_instrument(
        instrument_id,
        filtered_time_brackets,
        ot3_csound.SaturationSineTonesToSoundFileConverter(instrument_id),
    )


def _render_shadows():
    if compute.RENDER_MIDIFILES:
        for instrument_tag in (instruments.ID_VIOLIN, instruments.ID_SAXOPHONE):
            converters = (
                (
                    "",
                    shadows.TimeBracketContainerToShadowsConverter(
                        time_brackets_container.TIME_BRACKETS
                    ),
                ),
                (
                    "_fifth",
                    shadows.TimeBracketContainerToFifthParallelShadowsConverter(
                        time_brackets_container.TIME_BRACKETS
                    ),
                ),
            )
            for suffix, converter in converters:
                name = f"shadows_{instrument_tag}{suffix}.mid"
                converted_event = converter.convert(instrument_tag)
                midi_converter = ot3_midi.OT3InstrumentEventToMidiFileConverter(
                    name, apply_extrema=True, min_velocity=30, max_velocity=100
                )
                midi_converter.convert(converted_event)


def _render_saturation_sines():
    if compute.RENDER_SOUNDFILES:
        for instrument_id in instruments.SINE_VOICE_AND_CHANNEL_TO_ID.values():
            _render_saturation_sine(instrument_id)


def main():
    _render_shadows()
    # _render_violin()
    _render_saxophone()  # sax has to be rendered after violin
    # _render_saturation_sines()
    _render_bells()
    _render_modes()
    _render_sines()
    _render_drone()
