import typing

import abjad
import quicktions as fractions

from mutwo import converters
from mutwo import parameters


class Node(object):
    _mutwo_pitch_to_abjad_pitch_converter = (
        converters.frontends.abjad.MutwoPitchToHEJIAbjadPitchConverter(
            reference_pitch="e"
        )
    )

    def __init__(
        self,
        written_root_pitch: parameters.pitches.WesternPitch,
        original_sounding_root_pitch: parameters.pitches.JustIntonationPitch,
        distance_as_just_intonation_pitch: parameters.pitches.JustIntonationPitch,
    ):
        self._written_root_pitch = written_root_pitch
        self._distance_as_just_intonation_pitch = distance_as_just_intonation_pitch
        # written_pitch_as_mutwo_pitch = written_root_pitch.add(
        #     self.distance_as_western_pitch_interval, mutate=False
        # )
        # self._written_pitch = self._mutwo_pitch_to_abjad_pitch_converter.convert(
        #     written_pitch_as_mutwo_pitch
        # )
        self._written_pitch = self._mutwo_pitch_to_abjad_pitch_converter.convert(
            self._distance_as_just_intonation_pitch + original_sounding_root_pitch
        )

    def __repr__(self):
        return f"Node({self.written_pitch})"

    @property
    def distance_as_just_intonation_pitch(
        self,
    ) -> parameters.pitches.JustIntonationPitch:
        return self._distance_as_just_intonation_pitch

    @property
    def distance_as_western_pitch_interval(self) -> int:
        return round(self.distance_as_just_intonation_pitch.cents / 100)

    @property
    def written_pitch(self) -> abjad.NamedPitch:
        return self._written_pitch


class Harmonic(object):
    def __init__(
        self,
        written_root_pitch: parameters.pitches.WesternPitch,
        original_sounding_root_pitch: parameters.pitches.JustIntonationPitch,
        sounding_root_pitch: parameters.pitches.JustIntonationPitch,
        nth_harmonic: int,
    ):
        self._written_root_pitch = written_root_pitch
        self._sounding_root_pitch = sounding_root_pitch
        self._original_sounding_root_pitch = original_sounding_root_pitch
        self._nth_harmonic = nth_harmonic
        self._sounding_pitch = self.interval_to_root + sounding_root_pitch
        self._initialise_nodes()

    def _initialise_nodes(self):
        nodes = []
        for nth_node in range(1, self.nth_harmonic):
            ratio = fractions.Fraction(self.nth_harmonic, nth_node)
            if ratio.numerator == self.nth_harmonic:
                nodes.append(
                    Node(
                        self._written_root_pitch,
                        self._original_sounding_root_pitch,
                        parameters.pitches.JustIntonationPitch(ratio),
                    )
                )
        self._nodes = tuple(reversed(nodes))

    def __repr__(self):
        return f"Harmonic({self.nth_harmonic}, {self.sounding_pitch})"

    @property
    def nth_harmonic(self) -> int:
        return self._nth_harmonic

    @property
    def interval_to_root(self) -> parameters.pitches.JustIntonationPitch:
        return parameters.pitches.JustIntonationPitch(f"{self._nth_harmonic}/1")

    @property
    def nodes(self) -> typing.Tuple[Node, ...]:
        return self._nodes

    @property
    def sounding_pitch(self) -> parameters.pitches.JustIntonationPitch:
        return self._sounding_pitch


class String(object):
    _mutwo_pitch_to_abjad_pitch_converter = (
        converters.frontends.abjad.MutwoPitchToAbjadPitchConverter()
    )

    def __init__(
        self,
        nth_string: int,
        tuning_original: parameters.pitches.WesternPitch,
        tuning_original_as_just_intonation_pitch: parameters.pitches.JustIntonationPitch,
        tuning_retuned: parameters.pitches.JustIntonationPitch,
        n_harmonics: int = 6,
    ):
        self.nth_string = nth_string
        self.tuning_original = tuning_original
        self.tuning_original_as_just_intonation_pitch = (
            tuning_original_as_just_intonation_pitch
        )
        self.tuning_retuned = tuning_retuned
        self._n_harmonics = n_harmonics
        self._written_pitch = self._mutwo_pitch_to_abjad_pitch_converter.convert(
            self.tuning_original
        )

        self._initialise_harmonics()

    def _initialise_harmonics(self):
        self._harmonics = tuple(
            Harmonic(
                self.tuning_original,
                self.tuning_original_as_just_intonation_pitch,
                self.tuning_retuned,
                nth_harmonic,
            )
            for nth_harmonic in range(1, self._n_harmonics + 1)
        )

    def __repr__(self):
        return (
            f"String({self.nth_string}, {self.tuning_original}, {self.tuning_retuned})"
        )

    @property
    def harmonics(self) -> typing.Tuple[Harmonic, ...]:
        return self._harmonics

    @property
    def harmonic_pitches(
        self,
    ) -> typing.Tuple[parameters.pitches.JustIntonationPitch, ...]:
        return tuple(harmonic.sounding_pitch for harmonic in self.harmonics[1:])

    @property
    def written_pitch(self) -> abjad.NamedPitch:
        return self._written_pitch


class StringInstrument(object):
    def __init__(self, strings: typing.Tuple[String, ...]):
        self._strings = strings

    @property
    def strings(self):
        return self._strings

    def get_strings_with_pitch_in_harmonics(
        self, pitch_to_examine: parameters.pitches.JustIntonationPitch
    ) -> typing.Tuple[String, ...]:
        strings = []
        for string in self.strings:
            if pitch_to_examine in string.harmonic_pitches:
                strings.append(string)
        return tuple(strings)
