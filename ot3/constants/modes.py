import expenvelope

from mutwo import generators
from mutwo import parameters

from ot3 import constants as ot3_constants

N_VOICES = len(ot3_constants.instruments.MODE_IDS)
LIKELIHOOD_TO_ADD_TRIAD_TO_REST = expenvelope.Envelope.from_points(
    (0, 0), (0.3, 0), (0.4, 0.3), (0.7, 0.7), (1, 1)
)

SPAN_SIZE_TENDENCY = generators.koenig.Tendency(
    expenvelope.Envelope.from_points((0, 0.15), (0.5, 0.5), (1, 0.2)),
    expenvelope.Envelope.from_points((0, 0.3), (0.5, 0.7), (1, 0.4)),
    random_seed=99999999,
)


REGISTER_CHOICE = generators.generic.DynamicChoice(
    (2, 1, 0, -1),
    (
        expenvelope.Envelope.from_points((0, 1), (0.3, 0.4), (0.6, 0),),
        expenvelope.Envelope.from_points((0, 0.3), (0.3, 1), (0.5, 0.5), (0.7, 0)),
        expenvelope.Envelope.from_points(
            (0, 0), (0.2, 0), (0.3, 0.3), (0.5, 0.5), (0.7, 1), (1, 0.4)
        ),
        expenvelope.Envelope.from_points(
            (0, 0), (0.5, 0), (0.6, 0.3), (0.8, 0.5), (1, 1),
        ),
    ),
)

TRIAD0 = (
    parameters.pitches.JustIntonationPitch("1/1"),
    parameters.pitches.JustIntonationPitch("9/7"),
    parameters.pitches.JustIntonationPitch("3/2"),
)
TRIAD1 = (
    parameters.pitches.JustIntonationPitch("1/1"),
    parameters.pitches.JustIntonationPitch("7/6"),
    parameters.pitches.JustIntonationPitch("3/2"),
)
