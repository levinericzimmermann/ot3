import expenvelope

from mutwo import generators

DURATION_TENDENCY = generators.koenig.Tendency(
    expenvelope.Envelope.from_points(
        (0, 8), (0.2, 20), (0.4, 50), (0.55, 10), (0.6, 55), (0.68, 55), (1, 10)
    ),
    expenvelope.Envelope.from_points(
        (0, 15), (0.2, 28), (0.4, 54), (0.55, 14), (0.6, 75), (0.68, 75), (1, 28)
    ),
)


NOTE_DURATION_TENDENCY = generators.koenig.Tendency(
    expenvelope.Envelope.from_points(
        (0, 5),
        (0.2, 0.4),
        (0.3, 0.4),
        (0.4, 3),
        (0.55, 2),
        (0.65, 0.11),
        (0.75, 0.4),
        (1, 8),
    ),
    expenvelope.Envelope.from_points(
        (0, 7),
        (0.2, 1.2),
        (0.3, 1),
        (0.4, 7),
        (0.55, 5),
        (0.65, 0.39),
        (0.75, 1),
        (1, 10),
    ),
)

REST_DURATION_TENDENCY = generators.koenig.Tendency(
    expenvelope.Envelope.from_points(
        (0, 70), (0.3, 40), (0.45, 70), (0.6, 30), (0.8, 60), (1, 100)
    ),
    expenvelope.Envelope.from_points(
        (0, 95), (0.3, 60), (0.45, 100), (0.6, 40), (0.8, 90), (1, 120)
    ),
)

N_BELLS = 7


REGISTERS_TO_CHOOSE_FROM_DYNAMIC_CHOICE = generators.generic.DynamicChoice(
    ((3,), (3, 2), (3, 2, 1,), (3, 2, 1, 0), (1, 0),),
    (
        expenvelope.Envelope.from_points(
            (0, 1), (0.3, 0.2), (0.4, 0), (0.7, 0), (1, 1)
        ),
        expenvelope.Envelope.from_points(
            (0, 0.5),
            (0.2, 0.4),
            (0.4, 0.2),
            (0.5, 0),
            (0.65, 0),
            (0.7, 0.5),
            (0.875, 1),
            (1, 0),
        ),
        expenvelope.Envelope.from_points(
            (0, 0), (0.1, 0), (0.2, 0.3), (0.3, 0.5), (0.35, 0.8), (0.4, 0.8), (0.6, 0),
        ),
        expenvelope.Envelope.from_points(
            (0, 0), (0.3, 0), (0.4, 0.5), (0.6, 1), (0.7, 0.7), (0.8, 0.1)
        ),
        expenvelope.Envelope.from_points(
            (0, 0), (0.6, 0), (0.7, 0.1), (0.8, 0.8), (0.1, 0),
        ),
    ),
)


ARPEGGI_REGISTERS = generators.generic.DynamicChoice(
    (2, 1, 0),
    (
        # 2
        expenvelope.Envelope.from_points(
            (0, 0.7),
            (0.2, 1),
            (0.3, 0.2),
            (0.5, 0),
            (0.6, 0.2),
            (0.7, 0.15),
            (0.8, 0.3),
            (1, 0.8),
        ),
        # 1
        expenvelope.Envelope.from_points(
            (0, 0),
            (0.2, 0),
            (0.25, 0.5),
            (0.5, 0.5),
            (0.6, 1),
            (0.7, 1),
            (0.8, 0.4),
            (1, 0),
        ),
        # 0
        expenvelope.Envelope.from_points(
            (0, 0), (0.3, 0), (0.4, 0.2), (0.6, 1), (0.7, 0.9), (0.8, 0.2), (1, 0)
        ),
    ),
)

# in cents
ARPEGGI_REGISTER_RANGE = generators.koenig.Tendency(
    expenvelope.Envelope.from_points((0, 900), (1, 900)),
    expenvelope.Envelope.from_points((0, 1400), (1, 1400)),
)


N_PITCHES_IN_CHORD = generators.koenig.Tendency(
    expenvelope.Envelope.from_points((0, 2), (1, 2)),
    expenvelope.Envelope.from_points((0, 5), (1, 5)),
)
