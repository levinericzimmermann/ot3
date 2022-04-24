import abc
import copy
import functools
import itertools
import operator
import typing

import abjad
import expenvelope

from mutwo import converters
from mutwo import events
from mutwo import generators
from mutwo import parameters
from mutwo import utilities

from ot3 import constants as ot3_constants
from ot3 import parameters as ot3_parameters


class PickPitchesFromCurveAndWeightPairsConverter(
    converters.symmetrical.families.PickElementFromCurveAndWeightPairsConverter
):
    def __init__(
        self, instrument_ambitus: ot3_parameters.ambitus.Ambitus, seed: int = 10,
    ):
        super().__init__(None, seed)
        self.instrument_ambitus = instrument_ambitus

    @staticmethod
    def _get_potential_pitch_and_weight_pairs_from_one_curve_and_weight_pair(
        curve_and_weight_pair: typing.Tuple[events.families.PitchCurve, float]
    ) -> typing.Tuple[typing.Tuple[parameters.pitches.JustIntonationPitch, float], ...]:
        curve, weight = curve_and_weight_pair
        return tuple(
            (pitch, register_weight * weight)
            for pitch, register_weight in curve.registered_pitch_and_weight_pairs
        )

    @staticmethod
    def _get_potential_pitch_and_weight_pairs(
        curve_and_weight_pairs: typing.Tuple[
            typing.Tuple[events.families.PitchCurve, float], ...
        ]
    ) -> typing.Tuple[typing.Tuple[parameters.pitches.JustIntonationPitch, float], ...]:
        potential_pitch_and_weight_pairs = []
        for curve_and_weight_pair in curve_and_weight_pairs:
            potential_pitch_and_weight_pairs.extend(
                PickPitchesFromCurveAndWeightPairsConverter._get_potential_pitch_and_weight_pairs_from_one_curve_and_weight_pair(
                    curve_and_weight_pair
                )
            )
        return tuple(potential_pitch_and_weight_pairs)

    @staticmethod
    def _get_dynamic_according_to_weight_and_position(
        absolute_entry_delay: parameters.abc.DurationType, weight: float
    ) -> parameters.volumes.WesternVolume:
        absolute_position = (
            absolute_entry_delay / ot3_constants.families_pitch.FAMILIES_PITCH.duration
        )
        min_vol, max_vol = ot3_constants.tendencies.DYNAMIC_TENDENCY.range_at(
            absolute_position
        )
        dynamic = ot3_constants.definitions.DYNAMIC_RANGE[
            int(
                utilities.tools.scale(
                    utilities.tools.scale(weight, 0, 1, min_vol, max_vol),
                    0,
                    1,
                    0,
                    len(ot3_constants.definitions.DYNAMIC_RANGE),
                )
            )
        ]
        return parameters.volumes.WesternVolume(dynamic)

    def _filter_potential_pitches_by_ambitus(
        self,
        potential_pitch_and_weight_pairs: typing.Tuple[
            typing.Tuple[parameters.pitches.JustIntonationPitch, float], ...
        ],
    ) -> typing.Tuple[typing.Tuple[parameters.pitches.JustIntonationPitch, float], ...]:
        potential_pitches, _ = zip(*potential_pitch_and_weight_pairs)
        filtered_potential_pitches = self.instrument_ambitus.filter_members(
            potential_pitches
        )
        return tuple(
            (pitch, weight)
            for pitch, weight in potential_pitch_and_weight_pairs
            if pitch in filtered_potential_pitches
        )


class PickChordFromCurveAndWeightPairsConverter(
    PickPitchesFromCurveAndWeightPairsConverter
):
    def __init__(
        self,
        instrument_ambitus: ot3_parameters.ambitus.Ambitus,
        n_pitches_to_pick: int,
        seed: int = 10,
    ):
        super().__init__(instrument_ambitus, seed)
        self.n_pitches_to_pick = n_pitches_to_pick

    def _get_potential_chord_and_weight_pairs(
        self,
        potential_pitch_and_weight_pairs: typing.Tuple[
            typing.Tuple[parameters.pitches.JustIntonationPitch, float], ...
        ],
    ) -> typing.Tuple[
        typing.Tuple[typing.Tuple[parameters.pitches.JustIntonationPitch, ...], float],
        ...,
    ]:
        potential_chord_and_weight_pairs = []
        for combination in itertools.combinations(
            potential_pitch_and_weight_pairs, self.n_pitches_to_pick
        ):
            chord, weights = zip(*combination)
            resulting_intervals = tuple(
                pitch0 - pitch1 for pitch0, pitch1 in itertools.combinations(chord, 2)
            )
            # avoid seconds in chords
            if all(abs(interval.cents) > 200 for interval in resulting_intervals):
                weight = functools.reduce(operator.mul, weights)
                potential_chord_and_weight_pairs.append((chord, weight))
        return tuple(potential_chord_and_weight_pairs)

    def _convert_simple_event(
        self,
        event_to_convert: events.basic.SimpleEvent,
        absolute_entry_delay: parameters.abc.DurationType,
    ) -> events.basic.SimpleEvent:
        try:
            curve_and_weight_pairs = self._get_curve_and_weight_pairs(event_to_convert)
        except AttributeError:
            curve_and_weight_pairs = None
        converted_event = copy.copy(event_to_convert)
        if curve_and_weight_pairs:
            potential_pitch_and_weight_pairs = PickPitchesFromCurveAndWeightPairsConverter._get_potential_pitch_and_weight_pairs(
                curve_and_weight_pairs
            )
            potential_pitch_and_weight_pairs = self._filter_potential_pitches_by_ambitus(
                potential_pitch_and_weight_pairs
            )
            potential_chord_and_weight_pairs = self._get_potential_chord_and_weight_pairs(
                potential_pitch_and_weight_pairs
            )
            if potential_chord_and_weight_pairs:
                chords, weights = zip(*potential_chord_and_weight_pairs)
                choosen_pitches = tuple(
                    self._random.choice(
                        chords, p=utilities.tools.scale_sequence_to_sum(weights, 1)
                    )
                )
                weight_of_choosen_pitch = weights[chords.index(choosen_pitches)]
                dynamic = self._get_dynamic_according_to_weight_and_position(
                    absolute_entry_delay, weight_of_choosen_pitch
                )
                converted_event.volume = dynamic
                converted_event.pitch_or_pitches = choosen_pitches
            del converted_event.curve_and_weight_pairs

        return converted_event


class PickSaxMultiphonicsFromCurveAndWeightPairsConverter(
    PickChordFromCurveAndWeightPairsConverter
):
    def __init__(self):
        self._multiphonic_pitches_as_pitches = tuple(
            tuple(map(parameters.pitches.JustIntonationPitch, pitches))
            for pitches in ot3_constants.instruments.SAXOPHONE_MULTIPHONIC_PITCHES_TO_FINGERING.keys()
        )

        all_pitches = sorted(
            functools.reduce(operator.add, self._multiphonic_pitches_as_pitches)
        )
        ambitus = ot3_parameters.ambitus.Ambitus(min(all_pitches), max(all_pitches))
        super().__init__(ambitus, 0, 1000)

    def _get_potential_chord_and_weight_pairs(
        self,
        potential_pitch_and_weight_pairs: typing.Tuple[
            typing.Tuple[parameters.pitches.JustIntonationPitch, float], ...
        ],
    ) -> typing.Tuple[
        typing.Tuple[typing.Tuple[parameters.pitches.JustIntonationPitch, ...], float],
        ...,
    ]:
        available_pitches = tuple(
            map(operator.itemgetter(0), potential_pitch_and_weight_pairs)
        )
        potential_chord_and_weight_pairs = []

        for (
            multiphonic_pitches_as_exponents
        ) in (
            ot3_constants.instruments.SAXOPHONE_MULTIPHONIC_PITCHES_TO_FINGERING.keys()
        ):
            multiphonic_pitches = tuple(
                map(
                    parameters.pitches.JustIntonationPitch,
                    multiphonic_pitches_as_exponents,
                )
            )
            n_multiphonic_pitches = len(multiphonic_pitches)
            n_multiphonic_pitches_in_available_pitches = sum(
                1 for pitch in multiphonic_pitches if pitch in available_pitches
            )
            if n_multiphonic_pitches_in_available_pitches / n_multiphonic_pitches > 0.5:
                multiphonic_pitches_which_are_in_pitches = tuple(
                    filter(
                        lambda pitch: pitch in available_pitches, multiphonic_pitches
                    )
                )
                weight = sum(
                    potential_pitch_and_weight_pairs[available_pitches.index(pitch)][1]
                    for pitch in multiphonic_pitches_which_are_in_pitches
                )
                weight /= len(multiphonic_pitches_which_are_in_pitches)
                potential_chord_and_weight_pairs.append((multiphonic_pitches, weight))

        return tuple(potential_chord_and_weight_pairs)


class PickViolinFlageolettFromCurveAndWeightPairsConverter(
    PickPitchesFromCurveAndWeightPairsConverter
):
    def __init__(self, seed: int = 100):
        super().__init__(ot3_constants.instruments.AMBITUS_VIOLIN_HARMONICS, seed)

    @staticmethod
    def _get_potential_nodes(
        string: ot3_parameters.spectrals.String,
        harmonic_pitch: parameters.pitches.JustIntonationPitch,
    ) -> typing.Tuple[ot3_parameters.spectrals.Node, ...]:
        nth_harmonic = string.harmonic_pitches.index(harmonic_pitch) + 1
        harmonic = string.harmonics[nth_harmonic]
        return harmonic.nodes

    def _find_candidates_for_double_flageoletts(
        self,
        potential_pitch_and_weight_pairs: typing.Tuple[
            typing.Tuple[parameters.pitches.JustIntonationPitch, float], ...
        ],
    ) -> typing.Tuple[
        typing.Tuple[
            typing.Tuple[
                typing.Tuple[
                    parameters.pitches.JustIntonationPitch,
                    parameters.pitches.JustIntonationPitch,
                ],
                typing.Tuple[
                    ot3_parameters.spectrals.String, ot3_parameters.spectrals.String
                ],
                typing.Tuple[
                    ot3_parameters.spectrals.Node, ot3_parameters.spectrals.Node
                ],
            ],
            float,
        ],
        ...,
    ]:
        candidates_for_double_flageoletts = []
        for pitch_and_weight0, pitch_and_weight1 in itertools.combinations(
            potential_pitch_and_weight_pairs, 2
        ):
            strings0 = ot3_constants.instruments.VIOLIN_HARMONIC_TO_VIOLIN_STRINGS[
                pitch_and_weight0[0].exponents
            ]
            strings1 = ot3_constants.instruments.VIOLIN_HARMONIC_TO_VIOLIN_STRINGS[
                pitch_and_weight1[0].exponents
            ]

            for potential_string0, potential_string1 in itertools.product(
                strings0, strings1
            ):
                difference = abs(
                    potential_string0.nth_string - potential_string1.nth_string
                )
                if difference == 1:
                    nodes0 = self._get_potential_nodes(
                        potential_string0, pitch_and_weight0[0]
                    )
                    nodes1 = self._get_potential_nodes(
                        potential_string1, pitch_and_weight1[0]
                    )
                    for node0, node1 in itertools.product(tuple(nodes0), tuple(nodes1)):
                        distance_between_distances = abs(
                            node0.distance_as_just_intonation_pitch
                            - node1.distance_as_just_intonation_pitch
                        )
                        if (
                            distance_between_distances
                            < parameters.pitches.JustIntonationPitch("6/5")
                        ):
                            candidate = (
                                (
                                    (pitch_and_weight0[0], pitch_and_weight1[0]),
                                    (potential_string0, potential_string1),
                                    (node0, node1),
                                ),
                                (pitch_and_weight0[1] + pitch_and_weight1[1]) * 0.5,
                            )
                            candidates_for_double_flageoletts.append(candidate)
                            break
        return tuple(candidates_for_double_flageoletts)

    @staticmethod
    def _get_string_pitch_and_played_pitch_from_harmonic_pitch_and_string_and_nth_node(
        harmonic_pitch: parameters.pitches.JustIntonationPitch,
        string: ot3_parameters.spectrals.String,
        nth_node: int,
    ) -> typing.Tuple[abjad.NamedPitch, abjad.NamedPitch]:
        nth_harmonic = string.harmonic_pitches.index(harmonic_pitch) + 1
        harmonic = string.harmonics[nth_harmonic]
        return (string.written_pitch, harmonic.nodes[nth_node].written_pitch)

    def _convert_simple_event(
        self,
        event_to_convert: events.basic.SimpleEvent,
        absolute_entry_delay: parameters.abc.DurationType,
    ) -> events.basic.SimpleEvent:
        try:
            curve_and_weight_pairs = self._get_curve_and_weight_pairs(event_to_convert)
        except AttributeError:
            curve_and_weight_pairs = None
        converted_event = copy.copy(event_to_convert)
        if curve_and_weight_pairs:
            potential_pitch_and_weight_pairs = PickPitchesFromCurveAndWeightPairsConverter._get_potential_pitch_and_weight_pairs(
                curve_and_weight_pairs
            )
            potential_pitch_and_weight_pairs = self._filter_potential_pitches_by_ambitus(
                potential_pitch_and_weight_pairs
            )
            candidates_for_double_flageoletts = self._find_candidates_for_double_flageoletts(
                potential_pitch_and_weight_pairs
            )
            if candidates_for_double_flageoletts:
                candidates, weights = zip(*candidates_for_double_flageoletts)
                choosen_candidate = self._random.choice(
                    candidates, p=utilities.tools.scale_sequence_to_sum(weights, 1)
                )
                choosen_candidate = tuple(tuple(sub) for sub in choosen_candidate)
                weight_of_choosen_candidate = weights[
                    candidates.index(choosen_candidate)
                ]
                dynamic = self._get_dynamic_according_to_weight_and_position(
                    absolute_entry_delay, weight_of_choosen_candidate
                )
                converted_event.volume = dynamic
                choosen_pitches, choosen_strings, choosen_nodes = choosen_candidate
                converted_event.pitch_or_pitches = list(choosen_pitches)

                (string_pitch0, played_pitch0,) = (
                    choosen_strings[0].written_pitch,
                    choosen_nodes[0].written_pitch,
                )
                (string_pitch1, played_pitch1,) = (
                    choosen_strings[1].written_pitch,
                    choosen_nodes[1].written_pitch,
                )

                converted_event.playing_indicators.precise_double_harmonic.string_pitch0 = (
                    string_pitch0
                )
                converted_event.playing_indicators.precise_double_harmonic.played_pitch0 = (
                    played_pitch0
                )
                converted_event.playing_indicators.precise_double_harmonic.string_pitch1 = (
                    string_pitch1
                )
                converted_event.playing_indicators.precise_double_harmonic.played_pitch1 = (
                    played_pitch1
                )

            elif potential_pitch_and_weight_pairs:

                pitches, weights = zip(*potential_pitch_and_weight_pairs)
                choosen_pitch = self._random.choice(
                    pitches, p=utilities.tools.scale_sequence_to_sum(weights, 1)
                )
                weight_of_choosen_pitch = weights[pitches.index(choosen_pitch)]
                dynamic = self._get_dynamic_according_to_weight_and_position(
                    absolute_entry_delay, weight_of_choosen_pitch
                )
                converted_event.volume = dynamic
                converted_event.pitch_or_pitches = [choosen_pitch]
                (
                    string_pitch,
                    played_pitch,
                ) = self._get_string_pitch_and_played_pitch_from_harmonic_pitch_and_string_and_nth_node(
                    choosen_pitch,
                    ot3_constants.instruments.VIOLIN.get_strings_with_pitch_in_harmonics(
                        choosen_pitch
                    )[
                        0
                    ],
                    0,
                )

                converted_event.playing_indicators.precise_natural_harmonic.string_pitch = (
                    string_pitch
                )
                converted_event.playing_indicators.precise_natural_harmonic.played_pitch = (
                    played_pitch
                )

            del converted_event.curve_and_weight_pairs

        return converted_event


class PickSaxophoneFlageolettFromCurveAndWeightPairsConverter(
    PickPitchesFromCurveAndWeightPairsConverter
):
    def __init__(self, seed: int = 100):
        super().__init__(ot3_constants.instruments.AMBITUS_SAXOPHONE_HARMONICS, seed)

    @staticmethod
    def _get_string_pitch_and_played_pitch_from_harmonic_pitch_and_string_and_nth_node(
        harmonic_pitch: parameters.pitches.JustIntonationPitch,
        string: ot3_parameters.spectrals.String,
    ) -> typing.Tuple[abjad.NamedPitch, abjad.NamedPitch]:
        nth_harmonic = string.harmonic_pitches.index(harmonic_pitch) + 1
        harmonic = string.harmonics[nth_harmonic]
        written_root_pitch = harmonic._written_root_pitch
        interval_to_root = harmonic.interval_to_root
        interval_to_root_as_western_pitch_interval = round(interval_to_root.cents / 100)
        written_played_pitch = written_root_pitch.add(
            interval_to_root_as_western_pitch_interval, mutate=False
        )
        played_pitch = converters.frontends.abjad.MutwoPitchToAbjadPitchConverter().convert(
            written_played_pitch
        )
        return (string.written_pitch, played_pitch)

    def _convert_simple_event(
        self,
        event_to_convert: events.basic.SimpleEvent,
        absolute_entry_delay: parameters.abc.DurationType,
    ) -> events.basic.SimpleEvent:
        try:
            curve_and_weight_pairs = self._get_curve_and_weight_pairs(event_to_convert)
        except AttributeError:
            curve_and_weight_pairs = None
        converted_event = copy.copy(event_to_convert)
        if curve_and_weight_pairs:
            potential_pitch_and_weight_pairs = PickPitchesFromCurveAndWeightPairsConverter._get_potential_pitch_and_weight_pairs(
                curve_and_weight_pairs
            )
            potential_pitch_and_weight_pairs = self._filter_potential_pitches_by_ambitus(
                potential_pitch_and_weight_pairs
            )
            if potential_pitch_and_weight_pairs:

                pitches, weights = zip(*potential_pitch_and_weight_pairs)
                choosen_pitch = self._random.choice(
                    pitches, p=utilities.tools.scale_sequence_to_sum(weights, 1)
                )
                weight_of_choosen_pitch = weights[pitches.index(choosen_pitch)]
                dynamic = self._get_dynamic_according_to_weight_and_position(
                    absolute_entry_delay, weight_of_choosen_pitch
                )
                converted_event.volume = dynamic
                converted_event.pitch_or_pitches = [choosen_pitch]
                (
                    string_pitch,
                    played_pitch,
                ) = self._get_string_pitch_and_played_pitch_from_harmonic_pitch_and_string_and_nth_node(
                    choosen_pitch,
                    ot3_constants.instruments.SAXOPHONE.get_strings_with_pitch_in_harmonics(
                        choosen_pitch
                    )[
                        0
                    ],
                )

                converted_event.playing_indicators.precise_natural_harmonic.string_pitch = (
                    string_pitch
                )
                converted_event.playing_indicators.precise_natural_harmonic.played_pitch = (
                    played_pitch
                )
                converted_event.playing_indicators.precise_natural_harmonic.harmonic_note_head_style = (
                    False
                )
                converted_event.playing_indicators.precise_natural_harmonic.parenthesize_lower_note_head = (
                    True
                )

            del converted_event.curve_and_weight_pairs

        return converted_event


class PickPitchLineFromCurveAndWeightPairsConverter(
    PickPitchesFromCurveAndWeightPairsConverter
):
    def _calculate_new_weight(
        self,
        previous_weight: float,
        previous_pitch_cents: float,
        pitch: parameters.pitches.JustIntonationPitch,
    ) -> float:
        distance = abs(previous_pitch_cents - pitch.cents)
        min_distance = 50
        best_distance0 = 100
        best_distance1 = 230
        max_distance = 500
        distance_weight_envelope = expenvelope.Envelope.from_points(
            (min_distance, 0),
            (best_distance0, 1),
            (best_distance1, 1),
            (max_distance, 0),
        )
        return distance_weight_envelope.value_at(distance) * previous_weight

    def _find_pitches_for_phrase(
        self,
        curve_and_weight_pairs_per_event: typing.List[
            typing.Tuple[typing.Tuple[events.families.PitchCurve, float], ...]
        ],
    ) -> typing.Tuple[parameters.pitches.JustIntonationPitch, ...]:
        potential_pitch_and_weight_pairs_per_event = []
        for curve_and_weight_pairs in curve_and_weight_pairs_per_event:
            potential_pitch_and_weight_pairs = self._get_potential_pitch_and_weight_pairs(
                curve_and_weight_pairs
            )
            potential_pitch_and_weight_pairs = self._filter_potential_pitches_by_ambitus(
                potential_pitch_and_weight_pairs
            )
            potential_pitch_and_weight_pairs_per_event.append(
                potential_pitch_and_weight_pairs
            )

        pitch_per_event = []
        for (
            potential_pitch_and_weight_pairs
        ) in potential_pitch_and_weight_pairs_per_event:
            if pitch_per_event:
                previous_pitch = pitch_per_event[-1]
                if previous_pitch is not None:
                    previous_pitch_cents = previous_pitch.cents
                    potential_pitch_and_weight_pairs = tuple(
                        (
                            pitch,
                            self._calculate_new_weight(
                                weight, previous_pitch_cents, pitch
                            ),
                        )
                        for pitch, weight in potential_pitch_and_weight_pairs
                    )

            if potential_pitch_and_weight_pairs:
                pitches, weights = zip(*potential_pitch_and_weight_pairs)
                choosen_pitch = self._random.choice(
                    pitches, p=utilities.tools.scale_sequence_to_sum(weights, 1)
                )
                pitch_per_event.append(choosen_pitch)
            elif pitch_per_event:
                pitch_per_event.append(pitch_per_event[-1])
            else:
                pitch_per_event.append(None)
        return pitch_per_event

    def _apply_pitches_on_sequential_event(
        self, sequential_event_to_convert: events.basic.SequentialEvent,
    ):
        curve_and_weight_pairs_per_event = []
        melodic_phrases_indices = []
        start_index = None
        for event_index, simple_event in enumerate(sequential_event_to_convert):
            try:
                curve_and_weight_pairs = self._get_curve_and_weight_pairs(simple_event)
            except AttributeError:
                curve_and_weight_pairs = None

            if curve_and_weight_pairs is None or len(curve_and_weight_pairs) == 0:
                curve_and_weight_pairs = None
                if start_index:
                    melodic_phrases_indices.append((start_index, event_index))
                start_index = None

            if start_index is None and curve_and_weight_pairs:
                start_index = event_index

            curve_and_weight_pairs_per_event.append(curve_and_weight_pairs)

        if start_index is not None:
            melodic_phrases_indices.append((start_index, event_index + 1))

        for start_index, end_index in melodic_phrases_indices:
            pitch_per_event = self._find_pitches_for_phrase(
                curve_and_weight_pairs_per_event[start_index:end_index]
            )
            for index, pitch in enumerate(pitch_per_event):
                if pitch is not None:
                    sequential_event_to_convert[
                        index + start_index
                    ].pitch_or_pitches = [pitch]

    def _convert_sequential_event(
        self,
        sequential_event_to_convert: events.basic.SequentialEvent,
        absolute_entry_delay: parameters.abc.DurationType,
    ) -> events.basic.SequentialEvent:
        if isinstance(sequential_event_to_convert[0], events.basic.SimpleEvent):
            sequential_event_to_apply_pitches_to = sequential_event_to_convert.copy()
            self._apply_pitches_on_sequential_event(
                sequential_event_to_apply_pitches_to
            )
            return sequential_event_to_apply_pitches_to
        else:
            return super()._convert_sequential_event(
                sequential_event_to_convert, absolute_entry_delay
            )

    def convert(self, event_to_convert: events.abc.Event) -> events.abc.Event:
        return self._convert_event(event_to_convert, 0)


class PitchLine(abc.ABC):
    def __init__(
        self,
        start_pitch: parameters.pitches.JustIntonationPitch,
        instrument: ot3_parameters.spectrals.StringInstrument,
        border: float = 240,
    ):
        self._pitches = [start_pitch]
        self._weight = 0
        self._border = border
        self._candidates = []
        self._instrument = instrument

    @property
    def weight(self) -> int:
        return self._weight

    @property
    def candidates(self) -> typing.Sequence[parameters.pitches.JustIntonationPitch]:
        return self._candidates

    def find_candidates_and_set_weight(
        self,
        pitches_to_choose_from: typing.Sequence[parameters.pitches.JustIntonationPitch],
        direction: typing.Optional[bool] = None,
    ):
        good_candidates = []
        bad_candidates = []
        for pitch in pitches_to_choose_from:
            difference = (pitch - self._pitches[-1]).cents
            if direction is not None:
                pitch_direction = difference > 0
                if direction == pitch_direction:
                    is_addable = True
            else:
                is_addable = True

            if is_addable and difference != 0:
                absolute_difference = abs(difference)
                if absolute_difference <= self._border:
                    good_candidates.append(pitch)
                else:
                    bad_candidates.append((pitch, absolute_difference))

        if good_candidates:
            self._weight += 1
            self._candidates = tuple(good_candidates)

        elif bad_candidates:
            self._candidates = tuple(
                map(
                    operator.itemgetter(0),
                    sorted(bad_candidates, key=operator.itemgetter(1)),
                )
            )

    def jump(self) -> typing.Tuple["PitchLine", ...]:
        versions = []
        for candidate in self.candidates:
            version = copy.deepcopy(self)
            version._pitches.append(candidate)
            version._candidates = []
            versions.append(version)
        return tuple(versions)

    def _find_all_playing_options_for_pitch(
        self, pitch: parameters.pitches.JustIntonationPitch
    ) -> typing.Tuple[
        typing.Tuple[
            typing.Tuple[
                ot3_parameters.spectrals.String, ot3_parameters.spectrals.Node
            ],
            float,
        ],
        ...,
    ]:
        options = []
        strings_to_investigate = self._instrument.get_strings_with_pitch_in_harmonics(
            pitch
        )
        for string in strings_to_investigate:
            nth_harmonic = string.harmonic_pitches.index(pitch) + 1
            harmonic = string.harmonics[nth_harmonic]
            for node in harmonic.nodes:
                option = (
                    (string, node),
                    float(node.distance_as_just_intonation_pitch.inverse(mutate=False)),
                )
                options.append(option)
        return tuple(options)

    def resolve(
        self,
    ) -> typing.Tuple[
        typing.Tuple[
            parameters.pitches.JustIntonationPitch,
            ot3_parameters.spectrals.String,
            ot3_parameters.spectrals.Node,
        ],
        ...,
    ]:
        playing_options_per_pitch = tuple(
            self._find_all_playing_options_for_pitch(pitch) for pitch in self._pitches
        )

        candidates = []
        for start_playing_option in playing_options_per_pitch[0]:
            candidate = [start_playing_option]
            fitness = 0  # smaller is better
            for playing_options in playing_options_per_pitch[1:]:
                position_of_last_option = candidate[-1][-1]
                playing_option_candidates = []
                for playing_option in playing_options:
                    difference_to_previous_position = abs(
                        playing_option[-1] - position_of_last_option
                    )
                    playing_option_candidates.append(
                        (playing_option, difference_to_previous_position)
                    )
                best_playing_option_for_current_pitch, difference = min(
                    playing_option_candidates, key=operator.itemgetter(1)
                )
                fitness += difference
                candidate.append(best_playing_option_for_current_pitch)
            candidates.append((candidate, fitness))

        best_candidate, _ = min(candidates, key=operator.itemgetter(1))
        resolution = []
        for pitch, playing_option in zip(self._pitches, best_candidate):
            item = (pitch, playing_option[0][0], playing_option[0][1])
            resolution.append(item)
        return tuple(resolution)


class PickHarmonicsPitchLineFromCurveAndWeightPairsConverter(
    PickPitchesFromCurveAndWeightPairsConverter
):
    def __init__(
        self,
        instrument_ambitus: ot3_parameters.ambitus.Ambitus,
        instrument: ot3_parameters.spectrals.StringInstrument,
        seed: int = 10,
    ):
        super().__init__(None, seed)
        self._instrument = instrument
        self.instrument_ambitus = instrument_ambitus

    def _get_pitches_per_event(
        self, sequential_event_to_convert: events.basic.SequentialEvent
    ) -> typing.Tuple:
        pitches_per_event = []
        for simple_event in sequential_event_to_convert:
            try:
                curve_and_weight_pairs = self._get_curve_and_weight_pairs(simple_event)
            except AttributeError:
                curve_and_weight_pairs = None

            pitches = None
            if curve_and_weight_pairs:
                potential_pitch_and_weight_pairs = self._filter_potential_pitches_by_ambitus(
                    self._get_potential_pitch_and_weight_pairs(curve_and_weight_pairs)
                )
                if potential_pitch_and_weight_pairs:
                    pitches, _ = zip(*potential_pitch_and_weight_pairs)

            pitches_per_event.append(pitches)
        return tuple(pitches_per_event)

    def _apply_pitches_on_sequential_event(
        self, sequential_event_to_convert: events.basic.SequentialEvent,
    ):
        pitches_per_event = self._get_pitches_per_event(sequential_event_to_convert)
        if all((pitches is not None for pitches in pitches_per_event)):
            pitch_lines = tuple(
                PitchLine(start_pitch, self._instrument)
                for start_pitch in pitches_per_event[0]
            )
            for pitches in pitches_per_event[1:]:
                for pitch_line in pitch_lines:
                    pitch_line.find_candidates_and_set_weight(pitches)

                max_weight = max(pitch_line.weight for pitch_line in pitch_lines)
                new_pitch_lines = []
                for pitch_line in pitch_lines:
                    if pitch_line.weight == max_weight:
                        new_pitch_lines.extend(pitch_line.jump())

                pitch_lines = tuple(new_pitch_lines)
                if not pitch_lines:
                    break

            if pitch_lines:
                choosen_pitch_line = pitch_lines[0]
                resolution = choosen_pitch_line.resolve()
                for event, pitch_data in zip(sequential_event_to_convert, resolution):
                    pitch, string, node = pitch_data
                    event.pitch_or_pitches = [pitch]
                    event.playing_indicators.precise_natural_harmonic.string_pitch = (
                        string.written_pitch
                    )
                    event.playing_indicators.precise_natural_harmonic.played_pitch = (
                        node.written_pitch
                    )

    def _convert_sequential_event(
        self,
        sequential_event_to_convert: events.basic.SequentialEvent,
        absolute_entry_delay: parameters.abc.DurationType,
    ) -> events.basic.SequentialEvent:
        if isinstance(sequential_event_to_convert[0], events.basic.SimpleEvent):
            sequential_event_to_apply_pitches_to = sequential_event_to_convert.copy()
            self._apply_pitches_on_sequential_event(
                sequential_event_to_apply_pitches_to
            )
            return sequential_event_to_apply_pitches_to
        else:
            return super()._convert_sequential_event(
                sequential_event_to_convert, absolute_entry_delay
            )

    def convert(self, event_to_convert: events.abc.Event) -> events.abc.Event:
        return self._convert_event(event_to_convert, 0)


class PickBellPitchesFromCurveAndWeightPairsConverter(
    PickPitchesFromCurveAndWeightPairsConverter
):
    def __init__(
        self, seed: int = 10,
    ):
        super().__init__(None, seed)
        self._volume_range = (-30, 0)

    @staticmethod
    def _make_default_curve_and_weight_pairs(event_to_convert):
        return tuple(
            (
                events.families.PitchCurve(
                    parameters.pitches.JustIntonationPitch(ratio),
                    event_to_convert.duration,
                    expenvelope.Envelope.from_points((0, 1), (1, 1)),
                    "bell_curve",
                    register_to_weight={
                        -3: 0,
                        -2: 0,
                        -1: 0,
                        0: 0,
                        1: 0.2,
                        2: 1,
                        3: 0.6,
                    },
                ),
                weight,
            )
            for ratio, weight in zip(
                "35/32 1/1 7/6 7/4".split(" "), (0.05, 0.05, 0.025, 0.025)
            )
        )

    def _find_pitch_or_pitches(
        self,
        curve_and_weight_pairs: typing.Tuple[
            typing.Tuple[events.families.PitchCurve, float], ...
        ],
        allowed_register: typing.Tuple[int, ...],
        absolute_position: float,
    ) -> typing.List[parameters.pitches.JustIntonationPitch]:
        potential_pitch_and_weight_pairs = PickPitchesFromCurveAndWeightPairsConverter._get_potential_pitch_and_weight_pairs(
            curve_and_weight_pairs
        )
        filtered_pitch_and_weight_pairs = tuple(
            (pitch, weight)
            for pitch, weight in potential_pitch_and_weight_pairs
            if pitch.octave in allowed_register
        )
        if filtered_pitch_and_weight_pairs:
            pitches, weights = zip(*filtered_pitch_and_weight_pairs)
            choosen_pitch = self._random.choice(
                pitches, p=utilities.tools.scale_sequence_to_sum(weights, 1)
            )
            # get volume
            choosen_pitch_weight = weights[pitches.index(choosen_pitch)]
            return [choosen_pitch], choosen_pitch_weight

        return None, None

    def _convert_simple_event(
        self,
        event_to_convert: events.basic.SimpleEvent,
        absolute_entry_delay: parameters.abc.DurationType,
    ) -> events.basic.SimpleEvent:
        try:
            curve_and_weight_pairs = self._get_curve_and_weight_pairs(event_to_convert)
        except AttributeError:
            curve_and_weight_pairs = None

        absolute_position = (
            absolute_entry_delay / ot3_constants.families_pitch.FAMILIES_PITCH.duration
        )

        allowed_register = ot3_constants.clouds.REGISTERS_TO_CHOOSE_FROM_DYNAMIC_CHOICE.gamble_at(
            absolute_position
        )

        converted_event = copy.copy(event_to_convert)
        if curve_and_weight_pairs is not None:
            curve_and_weight_pairs = self._make_default_curve_and_weight_pairs(
                event_to_convert
            )
            allowed_register = (1, 2, 3)

        if curve_and_weight_pairs:
            pitch_or_pitches, choosen_pitch_weight = self._find_pitch_or_pitches(
                curve_and_weight_pairs, allowed_register, absolute_position
            )
            if pitch_or_pitches:
                converted_event.pitch_or_pitches = pitch_or_pitches

                volume = parameters.volumes.DecibelVolume(
                    utilities.tools.scale(
                        choosen_pitch_weight, 0, 1, *self._volume_range
                    )
                )
                converted_event.volume = volume

        return converted_event


class PickBellChordsFromCurveAndWeightPairsConverter(
    PickBellPitchesFromCurveAndWeightPairsConverter
):
    def _find_pitch_or_pitches(
        self,
        curve_and_weight_pairs: typing.Tuple[
            typing.Tuple[events.families.PitchCurve, float], ...
        ],
        allowed_register: typing.Tuple[int, ...],
        absolute_position: float,
    ) -> typing.List[parameters.pitches.JustIntonationPitch]:
        potential_pitch_and_weight_pairs = PickPitchesFromCurveAndWeightPairsConverter._get_potential_pitch_and_weight_pairs(
            curve_and_weight_pairs
        )
        filtered_pitch_and_weight_pairs = tuple(
            (pitch, weight)
            for pitch, weight in potential_pitch_and_weight_pairs
            if pitch.octave in allowed_register
        )
        if filtered_pitch_and_weight_pairs:
            pitches, weights = zip(*filtered_pitch_and_weight_pairs)
            n_pitches = round(
                ot3_constants.clouds.N_PITCHES_IN_CHORD.value_at(absolute_position)
            )
            n_available_pitches = len(pitches)
            if n_pitches > n_available_pitches:
                n_pitches = n_available_pitches
            choosen_pitches = list(
                self._random.choice(
                    pitches,
                    p=utilities.tools.scale_sequence_to_sum(weights, 1),
                    size=n_pitches,
                )
            )
            # get volume
            relevant_weights = [
                weights[pitches.index(choosen_pitch)]
                for choosen_pitch in choosen_pitches
            ]
            choosen_pitch_weight = sum(relevant_weights) / len(relevant_weights)
            return choosen_pitches, choosen_pitch_weight

        return None, None


class PickBellArpeggiFromCurveAndWeightPairsConverter(
    PickBellPitchesFromCurveAndWeightPairsConverter
):
    def __init__(self, *args, gray_code_length: int = 3, **kwargs):
        super().__init__(*args, **kwargs)
        self._gray_code_cycle = itertools.cycle(
            generators.gray.reflected_binary_code(gray_code_length, 2)
        )

    @staticmethod
    def _find_start_pitch(
        pitches_to_choose_from: typing.Tuple[
            parameters.pitches.JustIntonationPitch, ...
        ],
        ambitus: ot3_parameters.ambitus.Ambitus,
        direction: bool,
        previous_pitch: parameters.pitches.JustIntonationPitch,
    ) -> parameters.pitches.JustIntonationPitch:
        if direction:
            direction_operator = min
        else:
            direction_operator = max

        pitch_variants = functools.reduce(
            operator.add,
            (
                ambitus.find_all_pitch_variants(pitch)
                for pitch in pitches_to_choose_from
            ),
        )

        if previous_pitch and len(pitch_variants) > 1:
            pitch_variants = filter(
                lambda pitch: pitch != previous_pitch, pitch_variants
            )
        return direction_operator(pitch_variants)

    @staticmethod
    def _find_next_pitch(
        pitches_to_choose_from: typing.Tuple[
            parameters.pitches.JustIntonationPitch, ...
        ],
        ambitus: ot3_parameters.ambitus.Ambitus,
        direction: bool,
        previous_pitch: parameters.pitches.JustIntonationPitch,
    ) -> typing.Optional[parameters.pitches.JustIntonationPitch]:
        if previous_pitch:
            if direction:
                direction_operator = min
                filter_operator = lambda current_pitch: previous_pitch < current_pitch
            else:
                direction_operator = max
                filter_operator = lambda current_pitch: previous_pitch > current_pitch

            pitch_variants = functools.reduce(
                operator.add,
                (
                    ambitus.find_all_pitch_variants(pitch)
                    for pitch in pitches_to_choose_from
                ),
            )

            filtered_pitch_variants = tuple(filter(filter_operator, pitch_variants))
            if filtered_pitch_variants:
                return direction_operator(filtered_pitch_variants)

        return None

    def _get_ambitus(self, absolute_position: float) -> ot3_parameters.ambitus.Ambitus:
        register = ot3_constants.clouds.ARPEGGI_REGISTERS.gamble_at(absolute_position)
        register_span = ot3_constants.clouds.ARPEGGI_REGISTER_RANGE.value_at(
            absolute_position
        )
        amibuts_lower_border_in_cents = self._random.uniform(
            1200 * register, 1200 * (register + 1)
        )
        ambitus_higher_border_in_cents = amibuts_lower_border_in_cents + register_span
        ambitus_borders_in_cent = (
            amibuts_lower_border_in_cents,
            ambitus_higher_border_in_cents,
        )
        ambitus_borders_as_pitch = tuple(
            parameters.pitches.DirectPitch(
                parameters.pitches.DirectPitch.cents_to_ratio(cents)
                * ot3_constants.concert_pitch.CONCERT_PITCH_FREQUENCY
            )
            for cents in ambitus_borders_in_cent
        )
        return ot3_parameters.ambitus.Ambitus(*ambitus_borders_as_pitch)

    def _set_new_group(
        self, absolute_entry_delay: parameters.abc.DurationType,
    ):
        gray_code_iter = iter(next(self._gray_code_cycle))
        current_direction = next(gray_code_iter)
        absolute_position = (
            absolute_entry_delay / ot3_constants.families_pitch.FAMILIES_PITCH.duration
        )
        ambitus = self._get_ambitus(absolute_position)
        return gray_code_iter, current_direction, ambitus

    def _get_volume_for_current_pitch(
        self,
        choosen_pitch: parameters.pitches.JustIntonationPitch,
        pitches_to_choose_from: typing.Tuple[
            parameters.pitches.JustIntonationPitch, ...
        ],
        correlated_weights: typing.Tuple[float, ...],
    ):
        choosen_pitch_weight = (
            correlated_weights[
                pitches_to_choose_from.index(choosen_pitch.normalize(mutate=False))
            ]
            * 0.05
        )
        volume = parameters.volumes.DecibelVolume(
            utilities.tools.scale(choosen_pitch_weight, 0, 1, *self._volume_range)
        )
        return volume

    def _apply_pitches_on_simple_event(
        self,
        absolute_entry_delay: parameters.abc.DurationType,
        simple_event: events.basic.SimpleEvent,
        curve_and_weight_pairs: typing.Tuple[
            typing.Tuple[events.families.PitchCurve, float], ...
        ],
        gray_code_iter: typing.Iterable,
        current_direction: typing.Optional[bool],
        previous_pitch: typing.Optional[parameters.pitches.JustIntonationPitch],
        ambitus: typing.Optional[ot3_parameters.ambitus.Ambitus],
    ):
        pitches_to_choose_from = tuple(
            curve.pitch for curve, _ in curve_and_weight_pairs
        )
        correlated_weights = tuple(weight for _, weight in curve_and_weight_pairs)
        is_start_pitch = False
        if current_direction is None:
            try:
                current_direction = next(gray_code_iter)
            except StopIteration:
                gray_code_iter, current_direction, ambitus = self._set_new_group(
                    absolute_entry_delay
                )
            is_start_pitch = True

        if is_start_pitch:
            current_pitch = self._find_start_pitch(
                pitches_to_choose_from, ambitus, current_direction, previous_pitch
            )
        else:
            current_pitch = self._find_next_pitch(
                pitches_to_choose_from, ambitus, current_direction, previous_pitch
            )
            if current_pitch is None:
                return self._apply_pitches_on_simple_event(
                    absolute_entry_delay,
                    simple_event,
                    curve_and_weight_pairs,
                    gray_code_iter,
                    None,
                    previous_pitch,
                    ambitus,
                )

        simple_event.pitch_or_pitches = [current_pitch]
        simple_event.volume = self._get_volume_for_current_pitch(
            current_pitch, pitches_to_choose_from, correlated_weights
        )
        del simple_event.curve_and_weight_pairs

        return gray_code_iter, current_direction, current_pitch, ambitus

    def _apply_pitches_on_sequential_event(
        self,
        sequential_event_to_convert: events.basic.SequentialEvent,
        absolute_entry_delay: parameters.abc.DurationType,
    ):
        gray_code_iter = iter([])
        current_direction = None
        previous_pitch = None
        ambitus = None
        for absolute_entry_delay_of_event, simple_event in zip(
            sequential_event_to_convert.absolute_times, sequential_event_to_convert
        ):
            try:
                curve_and_weight_pairs = self._get_curve_and_weight_pairs(simple_event)
            except AttributeError:
                curve_and_weight_pairs = None

            if curve_and_weight_pairs:
                (
                    gray_code_iter,
                    current_direction,
                    previous_pitch,
                    ambitus,
                ) = self._apply_pitches_on_simple_event(
                    absolute_entry_delay_of_event + absolute_entry_delay,
                    simple_event,
                    curve_and_weight_pairs,
                    gray_code_iter,
                    current_direction,
                    previous_pitch,
                    ambitus,
                )

    def _convert_sequential_event(
        self,
        sequential_event_to_convert: events.basic.SequentialEvent,
        absolute_entry_delay: parameters.abc.DurationType,
    ) -> events.basic.SequentialEvent:
        if isinstance(sequential_event_to_convert[0], events.basic.SimpleEvent):
            sequential_event_to_apply_pitches_to = sequential_event_to_convert.copy()
            self._apply_pitches_on_sequential_event(
                sequential_event_to_apply_pitches_to, absolute_entry_delay,
            )
            return sequential_event_to_apply_pitches_to
        else:
            return super()._convert_sequential_event(
                sequential_event_to_convert, absolute_entry_delay
            )


class PickSaturationPitchFromCurveAndWeightPairsConverter(
    PickPitchesFromCurveAndWeightPairsConverter
):
    def __init__(
        self, seed: int = 1333333333333333333,
    ):
        super().__init__(
            ot3_parameters.ambitus.Ambitus(
                parameters.pitches.JustIntonationPitch("1/32"),
                parameters.pitches.JustIntonationPitch("32/1"),
            ),
            seed,
        )

    def _convert_simple_event(
        self,
        event_to_convert: events.basic.SimpleEvent,
        absolute_entry_delay: parameters.abc.DurationType,
    ) -> events.basic.SimpleEvent:
        try:
            curve_and_weight_pairs = self._get_curve_and_weight_pairs(event_to_convert)
        except AttributeError:
            curve_and_weight_pairs = None
        converted_event = copy.copy(event_to_convert)
        if curve_and_weight_pairs:
            potential_pitch_and_weight_pairs = tuple(
                (curve.pitch, weight) for curve, weight in curve_and_weight_pairs
            )
            pitches, weights = zip(*potential_pitch_and_weight_pairs)
            choosen_pitch = self._random.choice(
                pitches, p=utilities.tools.scale_sequence_to_sum(weights, 1)
            )
            weight_of_choosen_pitch = weights[pitches.index(choosen_pitch)]
            absolute_position = (
                absolute_entry_delay
                / ot3_constants.families_pitch.FAMILIES_PITCH.duration
            )
            choosen_register = ot3_constants.saturations.REGISTER_CHOICE.gamble_at(
                absolute_position
            )
            choosen_pitch = choosen_pitch.register(choosen_register, mutate=False)
            dynamic = utilities.tools.scale(weight_of_choosen_pitch, 0, 1, -30, 0)
            converted_event.volume = dynamic
            converted_event.pitch_or_pitches = [choosen_pitch]
            min_modulation = ot3_constants.saturations.MIN_MODULATION.value_at(
                absolute_position
            )
            converted_event.min_modulation = min_modulation
            likelihood_to_add_glissando = ot3_constants.saturations.LIKELIHOOD_ADD_GLISSANDO.value_at(
                absolute_position
            )
            if self._random.uniform(0, 1) < likelihood_to_add_glissando:
                glissando_factor = ot3_constants.saturations.GLISSANDO_FACTOR.value_at(
                    absolute_position
                )
                glissando_duration = ot3_constants.saturations.GLISSANDO_DURATION.value_at(
                    absolute_position
                )
            else:
                glissando_factor = 1
                glissando_duration = 1
            converted_event.glissando_factor = glissando_factor
            converted_event.glissando_duration = glissando_duration
            del converted_event.curve_and_weight_pairs

        return converted_event
