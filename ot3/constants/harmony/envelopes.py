import expenvelope

# how long one family takes
DURATION = expenvelope.Envelope.from_points(
    (0, 0),
    (0.3, 0.45),
    (0.4, 0.4),
    (0.45, 0.05),
    (0.55, 0.1),
    (0.65, 1),
    (0.85, 0.4),
    (1, 0.1),
)

# how fast the pendulum shakes (low values for slow harmonic changes, high values
# for fast harmonic changes)
SPEED = expenvelope.Envelope.from_points(
    (0, 0), (0.3, 0.85), (0.5, 0.4), (0.65, 1), (1, 0.1)
)

# how far the pendulum shall shake (1 for max distance in harmonic movement,
# 0 for almost no movement at all)
STRENGTH = expenvelope.Envelope.from_points((0, 0), (0.3, 0.85), (0.65, 1), (1, 0.4))

# how many seconds rest between each family
REST_DURATION = expenvelope.Envelope.from_points(
    (0, 0.2), (0.15, 0.3), (0.3, 0.84), (0.5, 0.3), (0.65, 0.96), (1, 0.4)
)
