import expenvelope

from mutwo import generators

from ot3 import constants
from ot3.converters import symmetrical as ot3_symmetrical


INSTRUMENT_ID_TO_TIME_BRACKET_FACTORY = {
    constants.instruments.ID_VIOLIN: generators.generic.DynamicChoice(
        (
            None,
            ot3_symmetrical.time_brackets.StartTimeToViolinCalligraphicLineConverter(
                constants.families_pitch.FAMILY_PITCH
            ),
            ot3_symmetrical.time_brackets.StartTimeToViolinGlissandiCalligraphicLineConverter(
                constants.families_pitch.FAMILY_PITCH_ONLY_WITH_NOTATEABLE_PITCHES,
            ),
            ot3_symmetrical.time_brackets.StartTimeToBowNoiseConverter(),
            ot3_symmetrical.time_brackets.StartTimeToHarmonicGlissandoConverter(),
            ot3_symmetrical.time_brackets.StartTimeToHarmonicMelodicPhraseConverter(
                constants.instruments.ID_VIOLIN,
                constants.families_pitch.FAMILY_PITCH,
                constants.instruments.AMBITUS_VIOLIN_HARMONICS,
                constants.instruments.VIOLIN,
            ),
            ot3_symmetrical.time_brackets.StartTimeToViolinMelodicPhraseConverter(
                constants.families_pitch.FAMILY_PITCH,
            ),
        ),
        (
            # nothing
            expenvelope.Envelope.from_points(
                (0, 2.1), (0.3, 2.9), (0.4, 0.9), (0.6, 0.7), (1, 2)
            ),
            # (double) flageolett calligraphic points
            expenvelope.Envelope.from_points(
                (0, 0),
                (0.027, 0),
                (0.035, 0.4),
                (0.175, 1),
                (0.2, 0.85),
                (0.4, 0.4),
                (0.65, 0.3),
                (1, 0.9),
            ),
            # violin glissando calligraphic points
            expenvelope.Envelope.from_points(
                (0, 0),
                (0.2, 0),
                (0.35, 0.6),
                (0.4, 0.1),
                (0.6, 1),
                (0.89, 0.5),
                (1, 0.2),
            ),
            # bow noise
            expenvelope.Envelope.from_points(
                (0, 0),
                (0.11, 0),
                (0.2, 0.68),
                (0.3, 0.49),
                (0.5, 0.35),
                (0.6, 0),
                (0.7, 0),
                (0.8, 0.5),
                (0.85, 0.7),
                (1, 0.4),
            ),
            # harmonic glissandi
            expenvelope.Envelope.from_points(
                (0, 0),
                (0.01, 0),
                (0.03, 0.7),
                (0.09, 0.5),
                (0.2, 0),
                (0.7, 0),
                (0.8, 0.1),
                (1, 0.3),
            ),
            # flageolett melodies
            expenvelope.Envelope.from_points(
                (0, 0),
                (0.03, 0),
                (0.09, 0.1),
                (0.2, 0.32),
                (0.4, 0.78),
                (0.5, 1),
                (1, 0.5),
            ),
            # ordinary melodies
            expenvelope.Envelope.from_points((0, 0), (0.4, 0), (0.6, 0.82), (0.85, 1),),
        ),
    ),
    constants.instruments.ID_SAXOPHONE: generators.generic.DynamicChoice(
        (
            None,
            ot3_symmetrical.time_brackets.StartTimeToSaxophoneHarmonicsCalligraphicLineConverter(
                constants.families_pitch.FAMILY_PITCH,
            ),
            ot3_symmetrical.time_brackets.StartTimeToSaxophoneCalligraphicLineConverter(
                constants.families_pitch.FAMILY_PITCH,
            ),
            ot3_symmetrical.time_brackets.StartTimeToSaxNoiseConverter(),
            ot3_symmetrical.time_brackets.StartTimeToSaxophoneMelodicPhraseConverter(
                constants.families_pitch.FAMILY_PITCH_ONLY_WITH_NOTATEABLE_PITCHES,
            ),
            ot3_symmetrical.time_brackets.StartTimeToSaxophoneMultiphonicsConverter(
                constants.families_pitch.FAMILY_PITCH_ONLY_WITH_NOTATEABLE_PITCHES,
            ),
            ot3_symmetrical.time_brackets.StartTimeToTeethOnReedConverter(),
        ),
        (
            # nothing
            expenvelope.Envelope.from_points(
                (0, 2), (0.2, 1.9), (0.3, 1.5), (0.4, 0.8), (0.6, 0.6), (1, 2)
            ),
            # calligraphic line with harmonics
            expenvelope.Envelope.from_points(
                (0, 0),
                (0.025, 0),
                (0.035, 0.3),
                (0.04, 0.6),
                (0.1, 0.8),
                (0.2, 1),
                (0.3, 0.5),
                (0.4, 0),
            ),
            # calligraphic line with "normal" pitches
            expenvelope.Envelope.from_points(
                (0, 0),
                (0.1, 0),
                (0.2, 0.6),
                (0.3, 1),
                (0.5, 0.5),
                (0.7, 0),
                (0.85, 0.2),
                (1, 1),
            ),
            # noise
            expenvelope.Envelope.from_points(
                (0, 0), (0.05, 0), (0.08, 0.5), (0.2, 0.3), (0.4, 0)
            ),
            # melodies
            expenvelope.Envelope.from_points(
                (0, 0),
                (0.2, 0),
                (0.24, 0.25),
                (0.35, 0.6),
                (0.5, 0.9),
                (0.65, 0.8),
                (1, 0.1),
            ),
            # multiphonics
            expenvelope.Envelope.from_points(
                (0, 0),
                (0.3, 0),
                (0.4, 0.585),
                (0.6, 0.9),
                (0.7, 1),
                (0.85, 0.35),
                (1, 0),
            ),
            # teeth on reed
            expenvelope.Envelope.from_points(
                (0, 0),
                (0.025, 0),
                (0.035, 0.2),
                (0.04, 0.4),
                (0.1, 0.5),
                (0.2, 0.3),
                (0.3, 0.05),
                (0.4, 0),
            ),
        ),
    ),
}
