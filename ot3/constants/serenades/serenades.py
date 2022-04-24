from mutwo import converters
from mutwo import events

from . import postprocess


def _convert(serenade: str):
    converter = converters.backends.mmml.MMMLConverter(
        converters.backends.mmml.MMMLEventsConverter(
            converters.backends.mmml.MMMLPitchesConverter(
                converters.backends.mmml.MMMLSingleJIPitchConverter()
            )
        )
    )

    converted_serenade = converter.convert(serenade)
    serenade = events.basic.SimultaneousEvent(
        [
            events.basic.TaggedSequentialEvent(event, tag=tag)
            for tag, event in converted_serenade.items()
        ]
    )

    return serenade


ID_SERENADE0 = "serenade0"
ID_SERENADE1 = "serenade1"
ID_SERENADE2 = "serenade2"


DEFINITIONS = {
    ID_SERENADE0: """
$violin

# first loop
r`2/1 1:1`4*p 3+:0`3/4
r`8 3--`8 1:1 7- 7- 3+:0 3- 3-- r`4
1:1 7+:0`3/4 3-`4 3+`3/4 3++5-`4 1:1`3/4

$saxophone

# first loop
1`2*p 3++7- 7- 3+:-1`1
1:0`2 7- 3++7- 1`1
7+3-`2 1 3++ 3+:-1`1
3+`2 3++:0 7+3- 1`2/1

# second loop
1`2*p 3++7- 7- 3+:-1`1
1:0`2 7- 3++7- 1`1
7+3-`2 1 3++ 3+:-1`1
3+`2 3++:0 7+3- 1`2/1
""",
    ID_SERENADE1: """
$violin
r`1 r`1

$saxophone
1`2*p 3++7- 7- 3+:-1`1
1:0`2 7- 3++7- 1`1
7+3-`2 1 3++ 3+:-1`1 3+`2 3++:0 7+3- 1`2/1
""",
    ID_SERENADE2: """
$violin
r`4 3+:0`2*p 7+3--`4 7+`1 r`4 7+3-`5/4
7+`4 5- 1:1`3/4 7+3--:0`2 r`2 7+`8 5-3-:1`8
1:1`4 1:1`4 5-:0`4 5-`4 r`4 3+`3/4 r`4
7+`2 3++:1`2 1`5/12 7+:0`1/6 3-5-:1 1:1`1 7+3-:0`1

$saxophone
1`2*p 7+3- 3++ 3+:-1`1 r`2
1:0`2/6 1`1/6 5+7+`4 1`4 7+3-`2 1`3/4 r`3/4
7+3-`2 1 3++ 3+:-1`3/4 r`4
3+`2 3++:0 7+3-`4 3++`4 1`2/1
""",
}

SERENADES = {name: _convert(content) for name, content in DEFINITIONS.items()}

TIME_SIGNATURES = {
    ID_SERENADE0: ((5, 2),),
    ID_SERENADE1: ((5, 2),),
    ID_SERENADE2: ((6, 2), (6, 2), (5, 2), (5, 2)),
}

START_TIMES = {
    ID_SERENADE0: (22 * 60) + 39,
    ID_SERENADE1: (35 * 60) + 21,
    ID_SERENADE2: (44 * 60) + 40,
}

TEMPOS = {ID_SERENADE0: 54, ID_SERENADE1: 58, ID_SERENADE2: 45}

postprocess.main(SERENADES)
