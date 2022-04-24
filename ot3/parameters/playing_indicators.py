import dataclasses
import typing

from mutwo.events import music_constants
from mutwo.parameters import abc
from mutwo.parameters import pitches
from mutwo.parameters import playing_indicators


@dataclasses.dataclass()
class ExplicitFermata(abc.ImplicitPlayingIndicator):
    fermata_type: typing.Optional[
        str
    ] = None  # TODO(for future usage add typing.Literal)
    waiting_range: typing.Optional[typing.Tuple[int, int]] = None


@dataclasses.dataclass()
class PreciseDoubleHarmonic(abc.ImplicitPlayingIndicator):
    string_pitch0: typing.Optional[pitches.WesternPitch] = None
    played_pitch0: typing.Optional[pitches.WesternPitch] = None

    string_pitch1: typing.Optional[pitches.WesternPitch] = None
    played_pitch1: typing.Optional[pitches.WesternPitch] = None


@dataclasses.dataclass()
class BendBefore(abc.ImplicitPlayingIndicator):
    bend_interval: typing.Optional[int] = None
    bend_length: typing.Optional[float] = 8


@dataclasses.dataclass()
class Fingering(abc.ImplicitPlayingIndicator):
    cc: typing.Optional[typing.Tuple[str, ...]] = None
    lh: typing.Optional[typing.Tuple[str, ...]] = None
    rh: typing.Optional[typing.Tuple[str, ...]] = None


@dataclasses.dataclass()
class CombinedFingerings(abc.ImplicitPlayingIndicator):
    fingerings: typing.Optional[typing.Tuple[Fingering, ...]] = None


@dataclasses.dataclass(frozen=True)
class OT2PlayingIndicatorCollection(playing_indicators.PlayingIndicatorCollection):
    # this is kind of redundant, but perhaps still better than without using
    # the `dataclasses` module
    bend_before: BendBefore = dataclasses.field(default_factory=BendBefore)
    bow_noise: abc.ExplicitPlayingIndicator = dataclasses.field(
        default_factory=abc.ExplicitPlayingIndicator
    )
    combined_fingerings: CombinedFingerings = dataclasses.field(
        default_factory=CombinedFingerings
    )
    empty_grace_container: abc.ExplicitPlayingIndicator = dataclasses.field(
        default_factory=abc.ExplicitPlayingIndicator
    )
    explicit_fermata: ExplicitFermata = dataclasses.field(
        default_factory=ExplicitFermata
    )
    fingering: Fingering = dataclasses.field(default_factory=Fingering)
    harmonic_glissando: abc.ExplicitPlayingIndicator = dataclasses.field(
        default_factory=abc.ExplicitPlayingIndicator
    )
    precise_double_harmonic: PreciseDoubleHarmonic = dataclasses.field(
        default_factory=PreciseDoubleHarmonic
    )
    teeth_on_reed: abc.ExplicitPlayingIndicator = dataclasses.field(
        default_factory=abc.ExplicitPlayingIndicator
    )


# set mutwo default values
music_constants.DEFAULT_PLAYING_INDICATORS_COLLECTION_CLASS = (
    OT2PlayingIndicatorCollection
)
