import expenvelope

from mutwo import generators

DYNAMIC_TENDENCY = generators.koenig.Tendency(
    expenvelope.Envelope.from_points((0, 0), (0.6, 0.8), (1, 0.2)),
    expenvelope.Envelope.from_points((0, 0.2), (0.6, 1), (1, 0.3)),
)
