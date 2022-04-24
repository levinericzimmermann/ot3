"""Sets concert pitch and reference pitch

The pitch class reference is dependent on the violin scordatura which
is (4/7 - 7/8 - 4/3 - 2/1): therefore the two highest pitches keep the same,
while the two lower pitches get slightly detuned. The highest violin pitch E
is the concert pitch 1/1.
"""

from mutwo.parameters import pitches
from mutwo.parameters import pitches_constants

CONCERT_PITCH_FREQUENCY_FOR_A = 442
REFERENCE = pitches.WesternPitch("e", 4, concert_pitch=CONCERT_PITCH_FREQUENCY_FOR_A)
CONCERT_PITCH_FREQUENCY = REFERENCE.frequency
pitches_constants.DEFAULT_CONCERT_PITCH = CONCERT_PITCH_FREQUENCY
