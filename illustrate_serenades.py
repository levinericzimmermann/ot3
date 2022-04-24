import abjad
import expenvelope

from mutwo import converters
from mutwo import events

path = "ot3/constants/serenades/illustrations"


def illustrate(
    name: str, serenade: events.basic.SimultaneousEvent, add_book_preamble: bool = True
):
    def _make_standard_sequential_converter():
        return converters.frontends.abjad.SequentialEventToAbjadVoiceConverter(
            converters.frontends.abjad.SequentialEventToQuantizedAbjadContainerConverter(
                time_signatures=(
                    abjad.TimeSignature((5, 2)),
                    abjad.TimeSignature((5, 2)),
                )
            ),
            mutwo_pitch_to_abjad_pitch_converter=converters.frontends.abjad.MutwoPitchToHEJIAbjadPitchConverter(
                "e"
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

    score_converter = _make_standard_score_converter()
    abjad_score = score_converter.convert(serenade)

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
    includes = ["ekme-heji-ref-c.ily"]
    if add_book_preamble:
        includes.append("lilypond-book-preamble.ly")
    lilypond_file = abjad.LilyPondFile(
        items=[abjad_score] + [paper_block], includes=includes,
    )
    abjad.persist.as_pdf(lilypond_file, f"{path}/{name}.pdf")


def render(name: str, serenade: events.basic.SimultaneousEvent):
    tempo_converter = converters.symmetrical.tempos.TempoConverter(
        expenvelope.Envelope.from_levels_and_durations(levels=[15, 15], durations=[1])
    )
    for sequential_event in serenade:
        converter = converters.frontends.midi.MidiFileConverter(
            f"{path}/{name}_{sequential_event.tag}.mid"
        )
        converter.convert(tempo_converter.convert(sequential_event))


if __name__ == "__main__":
    # setting concert pitch
    from mutwo import parameters

    parameters.pitches_constants.DEFAULT_CONCERT_PITCH = parameters.pitches.WesternPitch(
        "e", concert_pitch=442
    ).frequency

    from ot3.constants import serenades

    for name, serenade in serenades.SERENADES_AS_EVENTS.items():
        if name == "serenade2":
            render(name, serenade)
            illustrate(name, serenade)
