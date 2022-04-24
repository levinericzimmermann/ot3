from mutwo import converters
from mutwo import events

from . import definitions
from . import postprocess


class TempoBasedTimeBracketWithTimeSignatures(
    events.time_brackets.TempoBasedTimeBracket
):
    _class_specific_side_attributes = (
        events.time_brackets.TempoBasedTimeBracket._class_specific_side_attributes
        + ("time_signatures",)
    )

    def __init__(self, *args, time_signatures=((5, 2),), **kwargs):
        super().__init__(*args, **kwargs)
        self.time_signatures = time_signatures


def _convert_from_mmml(serenade: str):
    converter = converters.backends.mmml.MMMLConverter(
        converters.backends.mmml.MMMLEventsConverter(
            converters.backends.mmml.MMMLPitchesConverter(
                converters.backends.mmml.MMMLSingleJIPitchConverter()
            )
        )
    )

    converted_serenade = converter.convert(serenade)
    serenade = events.basic.SimultaneousEvent(
        [
            events.basic.TaggedSequentialEvent(event, tag=tag)
            for tag, event in converted_serenade.items()
        ]
    )

    # add cent deviations to violin notation
    for sequential_event in serenade:
        for simple_event in sequential_event:
            if (
                hasattr(simple_event, "pitch_or_pitches")
                and simple_event.pitch_or_pitches
            ):
                cent_deviations = []
                for pitch in simple_event.pitch_or_pitches:
                    deviation = pitch.cent_deviation_from_closest_western_pitch_class
                    if deviation != 0 and len(pitch.exponents) > 2:
                        cent_deviations.append(deviation)
                if cent_deviations:
                    simple_event.notation_indicators.cent_deviation.deviation = " ".join(
                        map(
                            lambda cent_deviation: str(round(cent_deviation)),
                            cent_deviations,
                        )
                    )

    return serenade


def _convert_to_time_bracket(
    name: str,
    serenade: events.basic.SimultaneousEvent[events.basic.TaggedSequentialEvent],
):
    voices = []
    for tagged_sequential_event in serenade:
        voices.append(
            events.basic.TaggedSimultaneousEvent(
                [events.basic.SequentialEvent(tuple(tagged_sequential_event))],
                tag=tagged_sequential_event.tag,
            )
        )

    start, tempo = definitions.START_TIMES[name], definitions.TEMPOS[name]
    beat_length_in_seconds = converters.symmetrical.tempos.TempoPointConverter().convert(
        tempo
    )
    end = start + (serenade.duration * 4 * beat_length_in_seconds)
    time_bracket = TempoBasedTimeBracketWithTimeSignatures(voices, start, end, tempo)
    time_bracket.time_signatures = definitions.TIME_SIGNATURES[name]
    return time_bracket


SERENADES_AS_EVENTS = {
    name: _convert_from_mmml(content)
    for name, content in definitions.DEFINITIONS.items()
}
postprocess.main(SERENADES_AS_EVENTS, definitions)

SERENADES = {
    name: _convert_to_time_bracket(name, serenade)
    for name, serenade in SERENADES_AS_EVENTS.items()
}

del postprocess
