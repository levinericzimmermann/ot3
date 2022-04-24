"""Global definitions for the generation of saturation tones.

These are single tones which get populated along one family
of pitch curves. Their main purpose is to add more saturation
to already existing structures. They use two different synthesis
techniques: simple sine tones and mode filters.
"""

import dataclasses
import itertools

import expenvelope

from mutwo import generators

TAIL = 5

N_VOICES_PER_TECHNIQUE = 6
# TECHNIQUES = ("sine",)
TECHNIQUES = ("sine", "mode")

DENSITY = expenvelope.Envelope.from_points(
    (0, 0.9),
    (0.1, 0.8),
    (0.2, 0.5),
    (0.3, 0.3),
    (0.4, 0.2),
    (0.5, 0.2),
    (0.6, 1),
    (0.65, 1),
    (0.7, 0.95),
    (0.8, 0.5),
    (0.9, 0.2),
)
DURATION = expenvelope.Envelope.from_points(
    (0, 8), (0.1, 12), (0.2, 9), (0.3, 6), (0.5, 5), (0.6, 5), (0.7, 12), (0.8, 14)
)
# 1: no uncertain area, 0: max length of uncertain area
TIME_BRACKET_RATIO = expenvelope.Envelope.from_points(
    (0, 0.9),
    (0.1, 0.8),
    (0.2, 0.7),
    (0.3, 0.3),
    (0.5, 0.2),
    (0.6, 1),
    (0.7, 0.7),
    (0.8, 0.5),
    (0.9, 0.1),
)
POPULATE_FAMILY_LIKELIHOOD = expenvelope.Envelope.from_points(
    (0, 1), (0.2, 1), (0.475, 0), (0.5, 0), (0.6, 1), (0.7, 1), (0.8, 0.5), (0.9, 0.1),
)
REGISTER_CHOICE = generators.generic.DynamicChoice(
    (5, 4, 3, 2, 1, 0, -1),
    (
        # 5
        expenvelope.Envelope.from_points((0, 1), (0.3, 0.35), (0.6, 0),),
        # 4
        expenvelope.Envelope.from_points((0, 0.75), (0.1, 1), (0.2, 0.3), (0.3, 0)),
        # 3
        expenvelope.Envelope.from_points(
            (0, 0.4), (0.2, 1), (0.3, 0.3), (0.4, 0), (0.6, 0), (0.7, 0.3)
        ),
        # 2
        expenvelope.Envelope.from_points(
            (0, 0.2),
            (0.1, 0.3),
            (0.2, 1),
            (0.3, 0.5),
            (0.5, 1),
            (0.6, 0.3),
            (0.775, 0.55),
        ),
        # 1
        expenvelope.Envelope.from_points(
            (0, 0), (0.2, 0), (0.3, 0.3), (0.5, 0.3), (0.6, 1), (0.7, 0.7)
        ),
        # 0
        expenvelope.Envelope.from_points(
            (0, 0), (0.2, 0), (0.5, 0), (0.6, 0.9), (0.7, 0.7), (0.8, 0.4), (0.9, 0)
        ),
        # -1
        expenvelope.Envelope.from_points(
            (0, 0), (0.55, 0), (0.6, 0.2), (0.7, 0.4), (0.8, 0.5), (0.9, 0.2)
        ),
    ),
)
MIN_MODULATION = expenvelope.Envelope.from_points(
    (0, 0), (0.3, 0.5), (0.5, 0.8), (0.9, 0.9)
)
LIKELIHOOD_ADD_GLISSANDO = expenvelope.Envelope.from_points(
    (0, 0.5), (0.1, 0.9), (0.2, 0.3), (0.3, 0), (0.5, 0.2)
)
GLISSANDO_DURATION = generators.koenig.Tendency(
    expenvelope.Envelope.from_points((0, 0.1), (0.1, 0.2), (0.2, 0.1),),
    expenvelope.Envelope.from_points((0, 0.2), (0.1, 0.5), (0.2, 0.2),),
    random_seed=3222,
)
GLISSANDO_FACTOR = generators.koenig.Tendency(
    expenvelope.Envelope.from_points((0, 0.75), (0.1, 0.5), (0.2, 0.7),),
    expenvelope.Envelope.from_points((0, 1.3), (0.1, 2), (0.2, 1.3),),
    random_seed=32,
)


@dataclasses.dataclass(frozen=True)
class Voice(object):
    nth_voice: int
    nth_channel: int
    technique: str


VOICE_CYCLE = []
for _nth_channel, _techniques_cycle in (
    (0, (TECHNIQUES[0], TECHNIQUES[1])),
    (1, (TECHNIQUES[1], TECHNIQUES[0])),
    (1, (TECHNIQUES[0], TECHNIQUES[1])),
    (0, (TECHNIQUES[1], TECHNIQUES[0])),
    # (0, (TECHNIQUES[0],)),
    # (1, (TECHNIQUES[0],)),
):
    _techniques_cycle = itertools.cycle(_techniques_cycle)
    for _nth_voice in range(N_VOICES_PER_TECHNIQUE):
        _technique = next(_techniques_cycle)
        _voice = Voice(
            nth_voice=_nth_voice, nth_channel=_nth_channel, technique=_technique
        )
        VOICE_CYCLE.append(_voice)

VOICE_CYCLE_BLUEPRINT = tuple(VOICE_CYCLE)
VOICE_CYCLE = itertools.cycle(VOICE_CYCLE)
