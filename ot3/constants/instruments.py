import functools
import operator
import typing
import warnings

from mutwo.parameters import pitches

from ot3.constants import concert_pitch
from ot3.constants import families_pitch
from ot3.constants import westminster
from ot3.parameters import ambitus
from ot3.parameters import playing_indicators
from ot3.parameters import spectrals


def _convert_western_pitch_to_ji_pitch(
    western_pitch: pitches.WesternPitch,
) -> pitches.JustIntonationPitch:
    difference_to_reference = western_pitch - concert_pitch.REFERENCE
    return pitches.JustIntonationPitch(
        pitches.JustIntonationPitch.cents_to_ratio(
            difference_to_reference * 100
        ).limit_denominator(1000)
    )


# instrument ids
ID_DRONE = "drone"
ID_VIOLIN = "violin"
ID_VIOLIN_FLAGEOLLETES = "violinFlageolettes"
ID_SAXOPHONE = "saxophone"

ID_INSTR_TO_ID_SINES = {
    ID_VIOLIN: ("sineViolin",),
    ID_SAXOPHONE: ("sineSaxophone",),
    ID_VIOLIN + "repetition": tuple(f"sineViolinRepetition{nth}" for nth in range(12)),
    ID_SAXOPHONE
    + "repetition": tuple(f"sineSaxophoneRepetition{nth}" for nth in range(12)),
}


INSTRUMENT_ID_TO_LONG_INSTRUMENT_NAME = {
    ID_VIOLIN: "violin",
    ID_DRONE: "drone",
    ID_SAXOPHONE: "alto sax",
}

INSTRUMENT_ID_TO_SHORT_INSTRUMENT_NAME = {
    ID_VIOLIN: "vl.",
    ID_DRONE: "d.",
    ID_SAXOPHONE: "a. s.",
}

INSTRUMENT_ID_TO_INDEX = {
    ID_VIOLIN: 0,
    ID_SAXOPHONE: 1,
    ID_DRONE: 2,
}

AMBITUS_DRONE_INSTRUMENT = ambitus.Ambitus(
    pitches.JustIntonationPitch("1/4"), pitches.JustIntonationPitch("1/2")
)

# how many voices (staves) one instrument owns
INSTRUMENT_TO_N_VOICES = {
    ID_DRONE: 1,
    ID_VIOLIN: 1,
    ID_SAXOPHONE: 1,
}


MODE_VOICE_AND_CHANNEL_TO_ID = {
    (nth_mode // 2, nth_mode % 2): f"mode_{nth_mode}" for nth_mode in range(12)
}

MODE_IDS = tuple(MODE_VOICE_AND_CHANNEL_TO_ID.values())


SINE_VOICE_AND_CHANNEL_TO_ID = {
    (nth_mode // 2, nth_mode % 2): f"saturation_sine_{nth_mode}"
    for nth_mode in range(12)
}

# ########################################################## #
#            saxophone specific definitions                  #
# ########################################################## #

AMBITUS_SAXOPHONE_WESTERN_PITCHES = ambitus.Ambitus(
    pitches.WesternPitch("g", 3),
    pitches.WesternPitch("c", 5),
)

_AMBITUS_SAXOPHONE_JUST_INTONATION_PITCHES = ambitus.Ambitus(
    _convert_western_pitch_to_ji_pitch(AMBITUS_SAXOPHONE_WESTERN_PITCHES.borders[0]),
    _convert_western_pitch_to_ji_pitch(AMBITUS_SAXOPHONE_WESTERN_PITCHES.borders[1]),
)

# how often a pitch should appear in the complete composition
# to get added to the saxophone ambitus
_minimal_appearence_of_pitch_to_get_added_to_saxophone_ambitus = 7
_saxophone_ambitus_pitch_set = []
for (
    pitch_as_exponent,
    how_often_pitch_appears,
) in families_pitch.NOTATEABLE_PITCH_TO_PITCH_COUNTER.items():
    pitch_as_pitch = pitches.JustIntonationPitch(pitch_as_exponent)
    shall_be_added_tests = (
        how_often_pitch_appears
        > _minimal_appearence_of_pitch_to_get_added_to_saxophone_ambitus,
        len(pitch_as_exponent) <= 2,
    )
    if any(shall_be_added_tests) and pitch_as_pitch not in (
        pitches.JustIntonationPitch("5/7"),
        pitches.JustIntonationPitch("7/10"),
        pitches.JustIntonationPitch("7/5"),
        pitches.JustIntonationPitch("10/7"),
    ):
        pitch_variants = (
            _AMBITUS_SAXOPHONE_JUST_INTONATION_PITCHES.find_all_pitch_variants(
                pitch_as_pitch
            )
        )
        _saxophone_ambitus_pitch_set.extend(pitch_variants)

_saxophone_ambitus_pitch_set.extend(westminster.INTONATIONS0)
_saxophone_ambitus_pitch_set.extend(westminster.INTONATIONS1)

_saxophone_ambitus_pitch_set.append(pitches.JustIntonationPitch("6/7"))
_saxophone_ambitus_pitch_set.append(pitches.JustIntonationPitch("5/8"))
_saxophone_ambitus_pitch_set.append(pitches.JustIntonationPitch("35/32"))
_saxophone_ambitus_pitch_set.append(pitches.JustIntonationPitch("5/4"))
_saxophone_ambitus_pitch_set.append(pitches.JustIntonationPitch("9/16"))
_saxophone_ambitus_pitch_set.append(pitches.JustIntonationPitch("64/81"))
_saxophone_ambitus_pitch_set.append(pitches.JustIntonationPitch("1/2"))

AMBITUS_SAXOPHONE_JUST_INTONATION_PITCHES = ambitus.SetBasedAmbitus(
    _saxophone_ambitus_pitch_set
)

N_HARMONICS_PER_FINGERING = (6, 3, 3)

# written pitches (transposed)
ORIGINAL_SAXOPHONE_TUNING_WESTERN_PITCHES = (
    pitches.WesternPitch("cs", 4),
    pitches.WesternPitch("fs", 4),
    pitches.WesternPitch("gs", 4),
)
# sounding pitches
SCORDATURA_SAXOPHONE_TUNING = (
    pitches.JustIntonationPitch("1/2"),
    pitches.JustIntonationPitch("2/3"),
    pitches.JustIntonationPitch("3/4"),
)

SAXOPHONE = spectrals.StringInstrument(
    tuple(
        spectrals.String(
            nth_string,
            original_tuning_of_string,
            scordatura_tuning_of_string,
            scordatura_tuning_of_string,
            n_harmonics,
        )
        for nth_string, original_tuning_of_string, scordatura_tuning_of_string, n_harmonics in zip(
            range(4),
            ORIGINAL_SAXOPHONE_TUNING_WESTERN_PITCHES,
            SCORDATURA_SAXOPHONE_TUNING,
            N_HARMONICS_PER_FINGERING,
        )
    )
)

# remove 1/1 and 2/1 (force to use 4/1)
SAXOPHONE.strings[0]._harmonics = SAXOPHONE.strings[0]._harmonics[2:]

AMBITUS_SAXOPHONE_HARMONICS = ambitus.SetBasedAmbitus(
    functools.reduce(
        operator.add,
        (string.harmonic_pitches for string in SAXOPHONE.strings),
    )
)

Exponents = typing.Tuple[int, ...]
SOUNDING_SAXOPHONE_PITCH_TO_WRITTEN_SAXOPHONE_PITCH_AND_CENT_DEVIATION: typing.Dict[
    Exponents, typing.Tuple[pitches.WesternPitch, typing.Optional[float]]
] = {}

_saxophone_root = pitches.WesternPitch("cs", 4)

for pitch in AMBITUS_SAXOPHONE_JUST_INTONATION_PITCHES.pitches:
    stepsize = round((pitch + pitches.JustIntonationPitch("2/1")).cents / 100)
    as_western_pitch = _saxophone_root.add(stepsize, mutate=False)
    if len(pitch.exponents) > 2:
        cent_deviation = pitch.cent_deviation_from_closest_western_pitch_class
    else:
        cent_deviation = None

    SOUNDING_SAXOPHONE_PITCH_TO_WRITTEN_SAXOPHONE_PITCH_AND_CENT_DEVIATION.update(
        {pitch.exponents: (as_western_pitch, cent_deviation)}
    )


SAXOPHONE_MULTIPHONIC_PITCHES_TO_MULTIPHONICS_DATA: typing.Dict[
    typing.Tuple[typing.Tuple[int, ...], ...], playing_indicators.Fingering
] = {
    tuple(pitch.exponents for pitch in multiphonic): data
    for multiphonic, data in (
        # kientzy 20
        (
            (
                pitches.JustIntonationPitch("35/32"),
                pitches.JustIntonationPitch("21/16"),
            ),
            (
                "kientzy 20",
                ("pp", "mp"),
                (
                    (pitches.WesternPitch("d", 5), 50),
                    (pitches.WesternPitch("f", 5), 50),
                ),
                playing_indicators.Fingering(
                    cc="one two three four six".split(" "),
                    lh=("low-bes",),
                    rh=("low-c", "high-fis"),
                ),
            ),
        ),
        # kientzy 25
        (
            (
                pitches.JustIntonationPitch("21/32"),
                pitches.JustIntonationPitch("35/16"),
                pitches.JustIntonationPitch("3/1"),
            ),
            (
                "kientzy 25",
                ("mp", "p"),
                (
                    (pitches.WesternPitch("f", 4), 50),
                    (pitches.WesternPitch("d", 6), 50),
                    (pitches.WesternPitch("gs", 6), 0),
                ),
                playing_indicators.Fingering(
                    cc="one two three five six".split(" "),
                    lh=("low-bes",),
                    rh=tuple([]),
                ),
            ),
        ),
        # kientzy 46
        (
            (
                pitches.JustIntonationPitch("1/1"),
                pitches.JustIntonationPitch("5/4"),
                pitches.JustIntonationPitch("9/4"),
            ),
            (
                "kientzy 46",
                ("p",),
                (
                    (pitches.WesternPitch("cs", 5), 0),
                    (pitches.WesternPitch("es", 5), 0),
                    (pitches.WesternPitch("ds", 6), 0),
                ),
                playing_indicators.Fingering(
                    cc="one two three four five six".split(" "),
                    lh=("b", "ees"),
                    rh=("fis",),
                ),
            ),
        ),
        # kientzy 65
        # REPLACED WITH WEISS 112!!
        # (
        #     (
        #         pitches.JustIntonationPitch("1/1"),
        #         pitches.JustIntonationPitch("7/6"),
        #     ),
        #     (
        #         "kientzy 65",
        #         ("pp", "p"),
        #         (
        #             (pitches.WesternPitch("cs", 5), 0),
        #             (pitches.WesternPitch("e", 5), -50),
        #         ),
        #         playing_indicators.Fingering(
        #             cc="one two three four six".split(" "),
        #             lh=tuple([]),
        #             rh=("low-c", "e"),
        #         ),
        #     ),
        # ),
        # weiss 112
        (
            (
                pitches.JustIntonationPitch("1/1"),
                pitches.JustIntonationPitch("7/6"),
            ),
            (
                "weiss 112",
                ("pp", "p"),
                (
                    (pitches.WesternPitch("cs", 5), 0),
                    (pitches.WesternPitch("e", 5), -50),
                ),
                playing_indicators.Fingering(
                    cc="one two three four six".split(" "),
                    lh=("front-f",),
                    rh=("low-c",),
                ),
            ),
        ),
        # kientzy 79 WITHOUT C3 ('e')!
        (
            (
                pitches.JustIntonationPitch("1/1"),
                pitches.JustIntonationPitch("6/5"),
            ),
            (
                "kientzy 79",
                ("pp", "p", "mf"),
                (
                    (pitches.WesternPitch("cs", 5), 0),
                    (pitches.WesternPitch("e", 5), 0),
                ),
                playing_indicators.Fingering(
                    cc="one two three four six".split(" "),
                    lh=("cis",),
                    # rh=("low-c", "e"),  # according to p. diederich without c3!
                    rh=("low-c",),
                ),
            ),
        ),
        # kientzy 102
        (
            (
                pitches.JustIntonationPitch("1/1"),
                pitches.JustIntonationPitch("6/5"),
                pitches.JustIntonationPitch("9/4"),
            ),
            (
                "adjusted kientzy 102",
                ("mp", "mf"),
                (
                    (pitches.WesternPitch("cs", 5), 0),
                    (pitches.WesternPitch("e", 5), 25),
                    (pitches.WesternPitch("ds", 6), 0),
                ),
                playing_indicators.Fingering(
                    cc="two three four six".split(" "), lh=("front-f",), rh=("low-c",)
                ),
            ),
        ),
    )
}

SAXOPHONE_MULTIPHONIC_PITCHES_TO_FINGERING: typing.Dict[
    typing.Tuple[typing.Tuple[int, ...], ...], playing_indicators.Fingering
] = {
    multiphonic_pitches: data[-1]
    for multiphonic_pitches, data in SAXOPHONE_MULTIPHONIC_PITCHES_TO_MULTIPHONICS_DATA.items()
}

SAXOPHONE_MICROTONAL_PITCHES_TO_COMBINED_FINGERINGS: typing.Dict[
    typing.Tuple[int, ...], playing_indicators.Fingering
] = {
    pitch.exponents: fingering
    for pitch, fingering in (
        (
            pitches.JustIntonationPitch("5/8"),
            playing_indicators.CombinedFingerings(
                fingerings=(
                    # the second one is better according to p. diederich
                    # playing_indicators.Fingering(
                    #     cc="one two three four six".split(" "),
                    #     lh=("low-bes",),
                    #     rh=("ees",),
                    # ),
                    playing_indicators.Fingering(
                        cc="one two three four six".split(" "),
                        lh=tuple([]),
                        rh=("ees",),
                    ),
                )
            ),
        ),
        (
            pitches.JustIntonationPitch("7/9"),
            playing_indicators.CombinedFingerings(
                fingerings=(
                    playing_indicators.Fingering(
                        cc="one two four".split(" "),
                        lh=tuple([]),
                        rh=tuple([]),
                    ),
                )
            ),
        ),
        (
            pitches.JustIntonationPitch("5/6"),
            playing_indicators.CombinedFingerings(
                fingerings=(
                    playing_indicators.Fingering(
                        cc="one three".split(" "),
                        lh=("gis", "bes"),
                        rh=tuple([]),
                    ),
                )
            ),
        ),
        (
            pitches.JustIntonationPitch("6/7"),
            playing_indicators.CombinedFingerings(
                fingerings=(
                    playing_indicators.Fingering(
                        cc=("one three",),
                        lh=("bes", "gis"),  # gis added by p. diederich
                        rh=("bes",),
                    ),
                )
            ),
        ),
        (
            pitches.JustIntonationPitch("7/8"),
            playing_indicators.CombinedFingerings(
                fingerings=(
                    playing_indicators.Fingering(
                        cc="one two three four five six".split(" "),
                        lh=tuple([]),
                        rh=("c",),
                    ),
                )
            ),
        ),
        (
            pitches.JustIntonationPitch("35/32"),
            playing_indicators.CombinedFingerings(
                fingerings=(
                    # playing_indicators.Fingering(
                    #     cc="one two".split(" "),
                    #     lh=("f",),
                    #     rh=tuple([]),
                    # ),
                    # the second option works better according to p. diederich
                    playing_indicators.Fingering(
                        cc="one two three four five six".split(" "),
                        lh=("T", "cis", "d", "ees"),
                        rh=tuple([]),
                    ),
                )
            ),
        ),
        (
            pitches.JustIntonationPitch("8/7"),
            playing_indicators.CombinedFingerings(
                fingerings=(
                    # the second specification is the best (according to p. diederich)
                    # playing_indicators.Fingering(
                    #     cc="one two three four five six".split(" "),
                    #     lh=("f", "T"),
                    #     rh=(
                    #         "ees",
                    #         "low-c",
                    #     ),
                    # ),
                    playing_indicators.Fingering(
                        cc=tuple([]),
                        lh=("ees", "f"),
                        rh=tuple([]),
                    ),
                    # avoid three different fingerings?
                    # playing_indicators.Fingering(
                    #     cc=tuple([]), lh=("ees", "f", "d"), rh=tuple([]),
                    # ),
                )
            ),
        ),
        (
            pitches.JustIntonationPitch("7/6"),
            playing_indicators.CombinedFingerings(
                fingerings=(
                    # both don't work (too deep) according to p. diederich!
                    # playing_indicators.Fingering(
                    #     cc="one two three four five six".split(" "),
                    #     lh=("d", "T", "ees", "f"),
                    #     rh=("ees",),
                    # ),
                    # playing_indicators.Fingering(
                    #     cc="one two three four five six".split(" "),
                    #     lh=("d", "T", "f"),
                    #     rh=("ees",),
                    # ),
                    playing_indicators.Fingering(
                        cc=tuple([]),
                        lh=tuple([]),
                        rh=("high-fis",),
                    ),
                )
            ),
        ),
        (
            pitches.JustIntonationPitch("5/4"),
            playing_indicators.CombinedFingerings(
                fingerings=(
                    playing_indicators.Fingering(
                        cc="one two three four six".split(" "),
                        lh=("T",),
                        rh=("low-c", "ees"),
                    ),
                )
            ),
        ),
        (
            pitches.JustIntonationPitch("9/7"),
            playing_indicators.CombinedFingerings(
                fingerings=(
                    playing_indicators.Fingering(
                        cc="one two three four five six".split(" "),
                        lh=("T", "low-bes"),
                        rh=("low-c",),
                    ),
                )
            ),
        ),
        (
            pitches.JustIntonationPitch("14/9"),
            playing_indicators.CombinedFingerings(
                fingerings=(
                    playing_indicators.Fingering(
                        cc="one two four".split(" "),
                        lh=("T",),
                        rh=tuple([]),
                    ),
                )
            ),
        ),
    )
}


def apply_saxophone_pitch(simple_event):
    if hasattr(simple_event, "pitch_or_pitches") and simple_event.pitch_or_pitches:
        if not simple_event.playing_indicators.precise_natural_harmonic.played_pitch:
            pitch_or_pitches = simple_event.pitch_or_pitches
            if len(pitch_or_pitches) > 1:
                pitches_as_exponents = tuple(
                    pitch.exponents for pitch in sorted(pitch_or_pitches)
                )
                try:
                    multiphonic_fingering = SAXOPHONE_MULTIPHONIC_PITCHES_TO_FINGERING[
                        pitches_as_exponents
                    ]
                except KeyError:
                    message = (
                        "Can't find fingering for multiphonic with pitches"
                        f" {pitch_or_pitches}!"
                    )
                    warnings.warn(message)
                    multiphonic_fingering = None

                if multiphonic_fingering:
                    pitches_to_write = [
                        pitch
                        for pitch, _ in SAXOPHONE_MULTIPHONIC_PITCHES_TO_MULTIPHONICS_DATA[
                            pitches_as_exponents
                        ][
                            -2
                        ]
                    ]
                    simple_event.pitch_or_pitches = pitches_to_write
                    (
                        simple_event.playing_indicators.fingering.cc,
                        simple_event.playing_indicators.fingering.rh,
                        simple_event.playing_indicators.fingering.lh,
                    ) = (
                        tuple(multiphonic_fingering.cc),
                        tuple(multiphonic_fingering.rh),
                        tuple(multiphonic_fingering.lh),
                    )

            else:
                pitch_to_investigate = pitch_or_pitches[0]
                if hasattr(pitch_to_investigate, "exponents"):
                    if len(pitch_to_investigate.exponents) > 2:
                        try:
                            microtonal_fingering = (
                                SAXOPHONE_MICROTONAL_PITCHES_TO_COMBINED_FINGERINGS[
                                    pitch_to_investigate.exponents
                                ]
                            )
                        except KeyError:
                            message = (
                                "No fingering defined yet for microtonal pitch"
                                f" {pitch_to_investigate}!"
                            )
                            warnings.warn(message)
                            microtonal_fingering = None

                        if microtonal_fingering:
                            simple_event.playing_indicators.combined_fingerings.fingerings = (
                                microtonal_fingering.fingerings
                            )

                    else:
                        if pitch_to_investigate == pitches.JustIntonationPitch("9/8"):
                            simple_event.notation_indicators.markup.content = (
                                "\\teeny { (C4) }"
                            )
                            simple_event.notation_indicators.markup.direction = "^"

                    try:
                        (
                            western_pitch,
                            cent_deviation,
                        ) = SOUNDING_SAXOPHONE_PITCH_TO_WRITTEN_SAXOPHONE_PITCH_AND_CENT_DEVIATION[
                            pitch_or_pitches[0].exponents
                        ]
                        simple_event.pitch_or_pitches = [western_pitch]
                        simple_event.notation_indicators.cent_deviation.deviation = (
                            cent_deviation
                        )
                    except KeyError:
                        message = (
                            "No deviation defined yet for microtonal pitch"
                            f" {pitch_or_pitches[0]}!"
                        )
                        warnings.warn(message)


# ########################################################## #
#            violin specific definitions                     #
# ########################################################## #

AMBITUS_VIOLIN_WESTERN_PITCHES = ambitus.Ambitus(
    pitches.WesternPitch("a", 4),
    pitches.WesternPitch("c", 6),
)

AMBITUS_VIOLIN_JUST_INTONATION_PITCHES = ambitus.Ambitus(
    _convert_western_pitch_to_ji_pitch(AMBITUS_VIOLIN_WESTERN_PITCHES.borders[0]),
    _convert_western_pitch_to_ji_pitch(AMBITUS_VIOLIN_WESTERN_PITCHES.borders[1]),
)


ORIGINAL_VIOLIN_TUNING = (
    pitches.JustIntonationPitch("16/27"),
    pitches.JustIntonationPitch("8/9"),
    pitches.JustIntonationPitch("4/3"),
    pitches.JustIntonationPitch("2/1"),
)

ORIGINAL_VIOLIN_TUNING_WESTERN_PITCHES = (
    pitches.WesternPitch("g", 3),
    pitches.WesternPitch("d", 4),
    pitches.WesternPitch("a", 4),
    pitches.WesternPitch("e", 5),
)

SCORDATURA_VIOLIN_TUNING = (
    pitches.JustIntonationPitch("7/12"),
    pitches.JustIntonationPitch("7/8"),
    pitches.JustIntonationPitch("4/3"),
    pitches.JustIntonationPitch("2/1"),
)

N_HARMONICS_PER_STRING = (7, 7, 7, 6)

VIOLIN = spectrals.StringInstrument(
    tuple(
        spectrals.String(
            nth_string,
            original_tuning_of_string,
            original_tuning_of_string_as_ji_pitch,
            scordatura_tuning_of_string,
            n_harmonics,
        )
        for nth_string, original_tuning_of_string, original_tuning_of_string_as_ji_pitch, scordatura_tuning_of_string, n_harmonics in zip(
            range(4),
            ORIGINAL_VIOLIN_TUNING_WESTERN_PITCHES,
            ORIGINAL_VIOLIN_TUNING,
            SCORDATURA_VIOLIN_TUNING,
            N_HARMONICS_PER_STRING,
        )
    )
)

# post-process node notation (should include hint for seventh partial)

AMBITUS_VIOLIN_HARMONICS = ambitus.SetBasedAmbitus(
    functools.reduce(
        operator.add,
        (string.harmonic_pitches for string in VIOLIN.strings),
    )
)

VIOLIN_HARMONIC_TO_VIOLIN_STRINGS = {
    harmonic.exponents: VIOLIN.get_strings_with_pitch_in_harmonics(harmonic)
    for harmonic in AMBITUS_VIOLIN_HARMONICS.pitches
}
