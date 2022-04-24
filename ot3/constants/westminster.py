import collections
import functools
import operator
import typing

import expenvelope
import quicktions as fractions

from mutwo import events
from mutwo import generators
from mutwo import parameters

from ot3 import utilities as ot3_utilities


class WestMinsterEvent(events.basic.SimpleEvent):
    def __init__(self, pitch_index: int, duration: parameters.abc.DurationType):
        self.pitch_index = pitch_index
        super().__init__(duration)


INTONATIONS0 = (
    parameters.pitches.JustIntonationPitch("3/4"),
    parameters.pitches.JustIntonationPitch("1/1"),
    parameters.pitches.JustIntonationPitch("8/7"),
    parameters.pitches.JustIntonationPitch("9/7"),
)

INTONATIONS1 = (
    parameters.pitches.JustIntonationPitch("3/4"),
    parameters.pitches.JustIntonationPitch("1/1"),
    parameters.pitches.JustIntonationPitch("9/8"),
    parameters.pitches.JustIntonationPitch("7/6"),
)

WESTMINSTER_MELODIES = events.basic.SequentialEvent(
    [
        events.basic.SequentialEvent(
            [
                WestMinsterEvent(3, fractions.Fraction(1, 4)),
                WestMinsterEvent(2, fractions.Fraction(1, 4)),
                WestMinsterEvent(1, fractions.Fraction(1, 4)),
                WestMinsterEvent(0, fractions.Fraction(1, 2)),
                # WestMinsterEvent(0, fractions.Fraction(1, 4)),
                # WestMinsterEvent(2, fractions.Fraction(1, 4)),
                # WestMinsterEvent(3, fractions.Fraction(1, 4)),
                # WestMinsterEvent(1, fractions.Fraction(1, 2)),
            ]
        ),
        events.basic.SequentialEvent(
            [
                WestMinsterEvent(1, fractions.Fraction(1, 4)),
                WestMinsterEvent(3, fractions.Fraction(1, 4)),
                WestMinsterEvent(2, fractions.Fraction(1, 4)),
                WestMinsterEvent(0, fractions.Fraction(1, 2)),
                WestMinsterEvent(1, fractions.Fraction(1, 4)),
                WestMinsterEvent(2, fractions.Fraction(1, 4)),
                WestMinsterEvent(3, fractions.Fraction(1, 4)),
                WestMinsterEvent(1, fractions.Fraction(1, 2)),
            ]
        ),
        events.basic.SequentialEvent(
            [
                WestMinsterEvent(3, fractions.Fraction(1, 4)),
                WestMinsterEvent(1, fractions.Fraction(1, 4)),
                WestMinsterEvent(2, fractions.Fraction(1, 4)),
                WestMinsterEvent(0, fractions.Fraction(1, 2)),
                WestMinsterEvent(0, fractions.Fraction(1, 4)),
                WestMinsterEvent(2, fractions.Fraction(1, 4)),
                WestMinsterEvent(3, fractions.Fraction(1, 4)),
                WestMinsterEvent(1, fractions.Fraction(1, 2)),
                WestMinsterEvent(3, fractions.Fraction(1, 4)),
                WestMinsterEvent(2, fractions.Fraction(1, 4)),
                WestMinsterEvent(1, fractions.Fraction(1, 4)),
                WestMinsterEvent(0, fractions.Fraction(1, 1)),
            ]
        ),
        events.basic.SequentialEvent(
            [
                WestMinsterEvent(1, fractions.Fraction(1, 4)),
                WestMinsterEvent(3, fractions.Fraction(1, 4)),
                WestMinsterEvent(2, fractions.Fraction(1, 4)),
                WestMinsterEvent(0, fractions.Fraction(1, 2)),
                WestMinsterEvent(1, fractions.Fraction(1, 4)),
                WestMinsterEvent(2, fractions.Fraction(1, 4)),
                WestMinsterEvent(3, fractions.Fraction(1, 4)),
                WestMinsterEvent(1, fractions.Fraction(1, 2)),
                WestMinsterEvent(3, fractions.Fraction(1, 4)),
                WestMinsterEvent(1, fractions.Fraction(1, 4)),
                WestMinsterEvent(2, fractions.Fraction(1, 4)),
                WestMinsterEvent(0, fractions.Fraction(1, 2)),
                WestMinsterEvent(0, fractions.Fraction(1, 4)),
                WestMinsterEvent(2, fractions.Fraction(1, 4)),
                WestMinsterEvent(3, fractions.Fraction(1, 4)),
                WestMinsterEvent(1, fractions.Fraction(1, 1)),
            ]
        ),
    ]
)

# how many times the melodic cycle get played
N_TIMES = 2


def _make_adapted_westminster_melodies(
    westminster_melodies: events.basic.SequentialEvent[
        events.basic.SequentialEvent[WestMinsterEvent]
    ],
    n_times: int,
    intonations0: typing.Tuple[parameters.pitches.JustIntonationPitch, ...],
    intonations1: typing.Tuple[parameters.pitches.JustIntonationPitch, ...],
):
    adapted_westminster_melodies = events.basic.SequentialEvent([])
    for _ in range(n_times):
        adapted_westminster_melodies.extend(westminster_melodies.copy())

    adapted_westminster_melodies.set_parameter(
        "duration", lambda duration: duration * 2
    )

    pitch_indices = functools.reduce(
        operator.add, adapted_westminster_melodies.get_parameter("pitch_index")
    )
    pitch_indices_counter = collections.Counter(pitch_indices)

    for pitch_index, pitch0, pitch1 in zip(range(4), intonations0, intonations1):
        n_appearences = pitch_indices_counter[pitch_index]
        distribution = generators.toussaint.euclidean(n_appearences, 2)
        pitch_per_position = iter(
            ot3_utilities.tools.not_fibonacci_transition(*distribution, pitch0, pitch1)
        )
        for phrase in adapted_westminster_melodies:
            for nth_event, westminster_event_or_note_like in enumerate(phrase):
                if (
                    hasattr(westminster_event_or_note_like, "pitch_index")
                    and westminster_event_or_note_like.pitch_index == pitch_index
                ):
                    phrase[nth_event] = events.music.NoteLike(
                        next(pitch_per_position),
                        westminster_event_or_note_like.duration,
                        "pp",
                    )
    return adapted_westminster_melodies


ADAPTED_WESTMINSTER_MELODIES = _make_adapted_westminster_melodies(
    WESTMINSTER_MELODIES, N_TIMES, INTONATIONS0, INTONATIONS1
)


TEMPO_ENVELOPE = expenvelope.Envelope.from_points((0, 45), (0.6, 60), (1, 30))
