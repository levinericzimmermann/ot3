import expenvelope

from mutwo import generators

from ot3 import constants as ot3_constants
from ot3 import utilities as ot3_utilities

VOLUMES_RANGES = ot3_utilities.equal_range_distributions.EqualRangeDistribution(
    -40, -6, 5
)(0)


ATTACK_DURATION_TENDENCY = generators.koenig.Tendency(
    expenvelope.Envelope.from_points((0, 5), (0.3, 3), (0.4, 5), (0.6, 0.2), (1, 5)),
    expenvelope.Envelope.from_points((0, 8), (0.3, 5), (0.4, 6), (0.6, 1.2), (1, 8)),
    random_seed=2,
)
RELEASE_DURATION_TENDENCY = generators.koenig.Tendency(
    expenvelope.Envelope.from_points((0, 5), (0.3, 3), (0.4, 5), (0.6, 0.2), (1, 5)),
    expenvelope.Envelope.from_points((0, 8), (0.3, 5), (0.4, 6), (0.6, 1.2), (1, 8)),
    random_seed=4,
)

ATTACK_WEIGHT_TENDENCY = generators.koenig.Tendency(
    expenvelope.Envelope.from_points(
        (0, 0), (0.3, 0.2), (0.4, 0.1), (0.6, 0.6), (1, 0.1)
    ),
    expenvelope.Envelope.from_points(
        (0, 0.1), (0.3, 0.25), (0.4, 0.15), (0.6, 0.65), (1, 0.12)
    ),
    random_seed=2,
)
RELEASE_WEIGHT_TENDENCY = generators.koenig.Tendency(
    expenvelope.Envelope.from_points(
        (0, 0), (0.3, 0.2), (0.4, 0.1), (0.6, 0.6), (1, 0.1)
    ),
    expenvelope.Envelope.from_points(
        (0, 0.1), (0.3, 0.25), (0.4, 0.15), (0.6, 0.65), (1, 0.12)
    ),
    random_seed=1999,
)

AVERAGE_DURATION_FOR_ONE_UNIT_TENDENCY = generators.koenig.Tendency(
    expenvelope.Envelope.from_points((0, 1), (0.3, 2), (0.6, 0.2), (1, 3)),
    expenvelope.Envelope.from_points((0, 2), (0.3, 4), (0.6, 1.2), (1, 5)),
    random_seed=32,
)


# how likely a new drone pitch becomes populated
ABSOLUTE_WEIGHT_TENDENCY = generators.koenig.Tendency(
    expenvelope.Envelope.from_points(
        (0, 0.42),
        (0.2, 0.4),
        (0.3, 0.6),
        (0.4, 0.45),
        (0.6, 0.9),
        (0.7, 0.94),
        (1, 0.55),
    ),
    expenvelope.Envelope.from_points(
        (0, 0.48), (0.3, 0.7), (0.4, 0.55), (0.6, 0.95), (0.7, 0.97), (1, 0.65)
    ),
    random_seed=111,
)


LOUDSPEAKER_TO_REGISTERS_TO_CHOOSE_FROM_DYNAMIC_CHOICES = {
    ot3_constants.loudspeakers.ID_RADIO_VIOLIN: generators.generic.DynamicChoice(
        ((2,), (2, 1), (2, 1), (1, 2), (0, 1),),
        (
            expenvelope.Envelope.from_points(
                (0, 1), (0.3, 0.2), (0.4, 0), (0.8, 0), (1, 0.7)
            ),
            expenvelope.Envelope.from_points(
                (0, 0), (0.2, 0.4), (0.4, 0.2), (0.8, 0), (1, 0.7)
            ),
            expenvelope.Envelope.from_points(
                (0, 0), (0.2, 0.1), (0.3, 0.4), (0.5, 0.7), (0.6, 0.1)
            ),
            expenvelope.Envelope.from_points(
                (0, 0), (0.2, 0.2), (0.3, 0.1), (0.4, 0.4), (0.5, 0.7), (0.6, 0.1)
            ),
            expenvelope.Envelope.from_points(
                (0, 0), (0.3, 0.2), (0.4, 0.5), (0.6, 1), (0.8, 0.5), (1, 0.4),
            ),
        ),
    ),
    ot3_constants.loudspeakers.ID_RADIO_SAXOPHONE: generators.generic.DynamicChoice(
        ((2,), (2, 1), (2, 1, 0), (1, 0), (0, -1),),
        (
            expenvelope.Envelope.from_points(
                (0, 1), (0.3, 0.2), (0.4, 0), (0.8, 0), (1, 0.8)
            ),
            expenvelope.Envelope.from_points(
                (0, 0), (0.2, 0.4), (0.4, 0.2), (0.8, 0), (1, 0.8)
            ),
            expenvelope.Envelope.from_points(
                (0, 0), (0.2, 0.1), (0.3, 0.4), (0.5, 0.7), (0.6, 0.1)
            ),
            expenvelope.Envelope.from_points(
                (0, 0), (0.2, 0), (0.3, 0.4), (0.4, 0.4), (0.5, 0.7), (0.6, 0.1)
            ),
            expenvelope.Envelope.from_points(
                (0, 0), (0.3, 0.2), (0.4, 0.5), (0.6, 1), (0.8, 0.6), (1, 0.5),
            ),
        ),
    ),
    ot3_constants.loudspeakers.ID_RADIO_BOAT0: generators.generic.DynamicChoice(
        ((2,), (2, 1), (1, 0), (1, 0, -1),),
        (
            expenvelope.Envelope.from_points(
                (0, 1), (0.3, 0.2), (0.4, 0), (0.8, 0), (1, 0.8)
            ),
            expenvelope.Envelope.from_points(
                (0, 0), (0.1, 0.4), (0.4, 0.2), (0.8, 0), (1, 0.8)
            ),
            expenvelope.Envelope.from_points(
                (0, 0), (0.2, 0.2), (0.3, 0.4), (0.5, 0.7), (0.6, 0.1)
            ),
            expenvelope.Envelope.from_points(
                (0, 0), (0.3, 0.3), (0.4, 0.5), (0.6, 1), (0.8, 0.6), (1, 0.5),
            ),
        ),
    ),
    ot3_constants.loudspeakers.ID_RADIO_BOAT1: generators.generic.DynamicChoice(
        ((2,), (2, 1), (1, 0), (1, 0, -1),),
        (
            expenvelope.Envelope.from_points(
                (0, 1), (0.3, 0.2), (0.4, 0), (0.8, 0), (1, 0.8)
            ),
            expenvelope.Envelope.from_points(
                (0, 0), (0.1, 0.4), (0.4, 0.2), (0.8, 0), (1, 0.8)
            ),
            expenvelope.Envelope.from_points(
                (0, 0), (0.2, 0.1), (0.3, 0.4), (0.5, 0.7), (0.6, 0.1)
            ),
            expenvelope.Envelope.from_points(
                (0, 0), (0.3, 0.2), (0.4, 0.3), (0.6, 1), (0.8, 0.6), (1, 0.5),
            ),
        ),
    ),
    ot3_constants.loudspeakers.ID_RADIO_BOAT2: generators.generic.DynamicChoice(
        ((2,), (2, 1), (1, 0), (1, 0, -1),),
        (
            expenvelope.Envelope.from_points(
                (0, 1), (0.3, 0.2), (0.4, 0), (0.8, 0), (1, 0.8)
            ),
            expenvelope.Envelope.from_points(
                (0, 0), (0.1, 0.4), (0.4, 0.2), (0.8, 0), (1, 0.8)
            ),
            expenvelope.Envelope.from_points(
                (0, 0), (0.1, 0.3), (0.3, 0.5), (0.5, 0.7), (0.6, 0.1)
            ),
            expenvelope.Envelope.from_points(
                (0, 0), (0.3, 0.1), (0.4, 0.4), (0.6, 1), (0.8, 0.6), (1, 0.5),
            ),
        ),
    ),
}
