from mutwo import parameters

MIN_DYNAMIC = "pp"
MAX_DYNAMIC = "mf"

DYNAMIC_RANGE = parameters.volumes_constants.STANDARD_DYNAMIC_INDICATOR[
    parameters.volumes_constants.STANDARD_DYNAMIC_INDICATOR.index(
        MIN_DYNAMIC
    ) : parameters.volumes_constants.STANDARD_DYNAMIC_INDICATOR.index(MAX_DYNAMIC)
    + 1
]
