import expenvelope

from ot3 import constants as ot3_constants

ID_SINE_TO_LIKELIHOOD = {
    ot3_constants.instruments.ID_INSTR_TO_ID_SINES[ot3_constants.instruments.ID_VIOLIN][
        0
    ]: expenvelope.Envelope.from_points((0, 1), (1, 1)),
    ot3_constants.instruments.ID_INSTR_TO_ID_SINES[
        ot3_constants.instruments.ID_SAXOPHONE
    ][0]: expenvelope.Envelope.from_points((0, 1), (1, 1)),
}


for likelihood_envelope, id_instr in (
    (
        expenvelope.Envelope.from_points(
            (0, 0.45), (0.3, 0.55), (0.6, 1), (0.8, 0.8), (1, 0.5)
        ),
        ot3_constants.instruments.ID_VIOLIN + "repetition",
    ),
    (
        expenvelope.Envelope.from_points(
            (0, 0.45), (0.3, 0.5), (0.6, 1), (0.8, 0.8), (1, 0.5)
        ),
        ot3_constants.instruments.ID_SAXOPHONE + "repetition",
    ),
):
    for id_sine in ot3_constants.instruments.ID_INSTR_TO_ID_SINES[id_instr]:
        ID_SINE_TO_LIKELIHOOD.update({id_sine: likelihood_envelope})
