import itertools
import typing

import expenvelope

from mutwo import converters
from mutwo import events
from mutwo import parameters
from mutwo import utilities

from ot3 import constants as ot3_constants
from ot3 import utilities as ot3_utilities


class FamiliesPitchToDronesConverter(converters.abc.Converter):
    loudspeaker_to_random_seed_for_brownian_rhythm = {
        ot3_constants.loudspeakers.ID_RADIO_VIOLIN: 10,
        ot3_constants.loudspeakers.ID_RADIO_SAXOPHONE: 100,
        ot3_constants.loudspeakers.ID_RADIO_BOAT0: 1000,
        ot3_constants.loudspeakers.ID_RADIO_BOAT1: 10000,
        ot3_constants.loudspeakers.ID_RADIO_BOAT2: 100000,
    }

    start_with_nth_voice = itertools.cycle((0, 1))
    loudspeaker_weights_cycle = itertools.cycle(tuple(itertools.permutations(range(5))))

    def __init__(self):
        import random as drone_random

        drone_random.seed(412412)
        self._random = drone_random

    def _make_blueprints_for_both_voices(
        self,
        average_duration_for_one_unit: float,
        family_of_pitch_curves: events.families.FamilyOfPitchCurves,
        random_seed_for_brownian_rhythm: int,
    ) -> events.basic.SequentialEvent[events.basic.SimultaneousEvent]:
        rhythmical_grid = ot3_utilities.tools.make_brownian_rhythm(
            family_of_pitch_curves.duration,
            average_duration_for_one_unit,
            random_seed_for_brownian_rhythm,
        )

        blueprint = events.basic.SimultaneousEvent(
            [events.basic.SequentialEvent([]) for _ in range(2)]
        )
        for nth_voice, cycle in enumerate(
            (
                itertools.cycle(
                    ((3, events.music.NoteLike), (1, events.basic.SimpleEvent))
                ),
                itertools.cycle(
                    ((1, events.basic.SimpleEvent), (3, events.music.NoteLike))
                ),
            )
        ):
            position = 0
            while position < len(rhythmical_grid):
                n_beats, event_class = next(cycle)
                duration = sum(rhythmical_grid[position : position + n_beats])
                try:
                    event = event_class(duration=duration)
                except TypeError:
                    event = event_class(duration)
                blueprint[nth_voice].append(event)
                position += n_beats

        start_with_nth_voice = next(self.start_with_nth_voice)
        if start_with_nth_voice == 1:
            blueprint.reverse()

        return blueprint

    def _find_pitch_for_event(
        self,
        absolute_time: parameters.abc.DurationType,
        event: events.music.NoteLike,
        family_of_pitch_curves: events.families.FamilyOfPitchCurves,
    ) -> typing.Tuple[parameters.pitches.JustIntonationPitch, float]:
        filtered_family = family_of_pitch_curves.filter(
            lambda event: event.duration > absolute_time, mutate=False
        )
        filtered_family.cut_out(absolute_time, absolute_time + event.duration)
        filtered_family.filter_inactive_curves()
        pitch_and_weight_pairs = tuple(
            (pitch_curve.pitch, pitch_curve.weight_curve.average_level())
            for pitch_curve in filtered_family
        )
        pitches, weights = zip(*pitch_and_weight_pairs)
        choosen_pitch = self._random.choices(pitches, weights, k=1)[0]
        choosen_pitch_weight = weights[pitches.index(choosen_pitch)]
        return choosen_pitch, choosen_pitch_weight

    def _register_pitch(
        self,
        pitch_to_register: parameters.pitches.JustIntonationPitch,
        registers_to_choose_from: typing.Tuple[int, ...],
    ):
        choosen_register = self._random.choice(registers_to_choose_from)
        return pitch_to_register.register(choosen_register, mutate=False)

    def _find_volume_for_event(
        self,
        absolute_time: parameters.abc.DurationType,
        absolute_position: float,
        weight_curve: expenvelope.Envelope,
        attack_release_envelope: expenvelope.Envelope,
        pitch_weight: float,
    ) -> parameters.volumes.DecibelVolume:
        loudspeaker_weight = weight_curve.value_at(absolute_time)
        attack_release_envelope_factor = attack_release_envelope.value_at(
            absolute_position
        )

        volume_range = ot3_constants.drone.VOLUMES_RANGES[
            int(round(loudspeaker_weight))
        ]
        volume_in_decibel = utilities.tools.scale(pitch_weight, 0, 1, *volume_range)
        volume_as_amplitude_ratio = (
            parameters.abc.Volume.decibel_to_amplitude_ratio(volume_in_decibel)
            * attack_release_envelope_factor
        )
        volume_in_decibel = parameters.abc.Volume.amplitude_ratio_to_decibel(
            volume_as_amplitude_ratio
        )
        return parameters.volumes.DecibelVolume(volume_in_decibel)

    def _assign_parameters_to_voice(
        self,
        loudspeaker_id: str,
        voice: events.basic.SequentialEvent,
        weight_curve: expenvelope.Envelope,
        attack_release_envelope: expenvelope.Envelope,
        family_of_pitch_curves: events.families.FamilyOfPitchCurves,
        populate_weight: float,
        global_absolute_position: float,
    ):
        for absolute_time, event in zip(voice.absolute_times, voice):
            if isinstance(event, events.music.NoteLike):
                registers_to_choose_from = ot3_constants.drone.LOUDSPEAKER_TO_REGISTERS_TO_CHOOSE_FROM_DYNAMIC_CHOICES[
                    loudspeaker_id
                ].gamble_at(
                    global_absolute_position
                )
                absolute_position = absolute_time / family_of_pitch_curves.duration
                attack_release_weight = attack_release_envelope.value_at(
                    absolute_position
                )
                resulting_weight = populate_weight * attack_release_weight
                if self._random.random() < resulting_weight:
                    choosen_pitch, pitch_weight = self._find_pitch_for_event(
                        absolute_time, event, family_of_pitch_curves,
                    )
                    event.pitch_or_pitches = self._register_pitch(
                        choosen_pitch, registers_to_choose_from
                    )
                    event.volume = self._find_volume_for_event(
                        absolute_time,
                        absolute_position,
                        weight_curve,
                        attack_release_envelope,
                        pitch_weight,
                    )
                else:
                    event.pitch_or_pitches = []

    def _convert_family(
        self,
        loudspeaker_id: str,
        average_duration_for_one_unit: float,
        family_of_pitch_curves: events.families.FamilyOfPitchCurves,
        simultaneous_event: events.basic.SimultaneousEvent[
            events.basic.SequentialEvent
        ],
        weight_curve: expenvelope.Envelope,
        attack_release_envelope: expenvelope.Envelope,
        random_seed_for_brownian_rhythm: int,
        populate_weight: float,
        global_absolute_position: float,
    ):
        blueprint = self._make_blueprints_for_both_voices(
            average_duration_for_one_unit,
            family_of_pitch_curves,
            random_seed_for_brownian_rhythm,
        )

        for nth_voice, voice in enumerate(blueprint):
            self._assign_parameters_to_voice(
                loudspeaker_id,
                voice,
                weight_curve,
                attack_release_envelope,
                family_of_pitch_curves,
                populate_weight,
                global_absolute_position,
            )
            simultaneous_event[nth_voice].extend(voice)

    def _make_weight_curve_for_each_loudspeaker(
        self,
        family_of_pitch_curves: events.families.FamilyOfPitchCurves,
        average_duration_for_one_unit: float,
    ) -> typing.Dict[str, expenvelope.Envelope]:
        rhythmical_grid = ot3_utilities.tools.make_brownian_rhythm(
            family_of_pitch_curves.duration, average_duration_for_one_unit * 3, 13
        )
        weights_per_point = tuple(
            next(self.loudspeaker_weights_cycle) for _ in rhythmical_grid
        )
        weights_per_loudspeaker = zip(*weights_per_point)
        weight_curve_per_loudspeaker = {}
        for loudspeaker_id, weights in zip(
            ot3_constants.loudspeakers.LOUDSPEAKERS, weights_per_loudspeaker
        ):
            weight_points = []
            for absolute_time, weight in zip(
                utilities.tools.accumulate_from_zero(rhythmical_grid), weights
            ):
                weight_points.append(
                    (absolute_time / family_of_pitch_curves.duration, weight)
                )
            weight_curve = expenvelope.Envelope.from_points(*weight_points)
            weight_curve_per_loudspeaker.update({loudspeaker_id: weight_curve})

        return weight_curve_per_loudspeaker

    def _make_attack_release_envelope(
        self,
        family_of_pitch_curves: events.families.FamilyOfPitchCurves,
        absolute_position: float,
    ) -> expenvelope.Envelope:
        attack_duration = ot3_constants.drone.ATTACK_DURATION_TENDENCY.value_at(
            absolute_position
        )
        release_duration = ot3_constants.drone.RELEASE_DURATION_TENDENCY.value_at(
            absolute_position
        )
        attack_weight = ot3_constants.drone.ATTACK_WEIGHT_TENDENCY.value_at(
            absolute_position
        )
        release_weight = ot3_constants.drone.RELEASE_WEIGHT_TENDENCY.value_at(
            absolute_position
        )
        absolute_attack_duration = attack_duration / family_of_pitch_curves.duration
        absolute_release_duration = release_duration / family_of_pitch_curves.duration
        return expenvelope.Envelope.from_points(
            (0, attack_weight),
            (absolute_attack_duration, 1),
            (1 - absolute_attack_duration - absolute_release_duration, 1),
            (1, release_weight),
        )

    def _convert_family_for_each_loudspeaker(
        self,
        family_of_pitch_curves: events.families.FamilyOfPitchCurves,
        loudspeaker_to_simultaneous_event: typing.Dict[
            str,
            events.basic.SimultaneousEvent[
                events.basic.SequentialEvent[
                    typing.Union[events.music.NoteLike, events.basic.SimpleEvent]
                ]
            ],
        ],
        absolute_time: parameters.abc.DurationType,
        duration_of_families_pitch: parameters.abc.DurationType,
    ):
        absolute_position = absolute_time / duration_of_families_pitch
        filtered_family_of_pitch_curves = family_of_pitch_curves.filter_curves_with_tag(
            "root", mutate=False
        )
        average_duration_for_one_unit = ot3_constants.drone.AVERAGE_DURATION_FOR_ONE_UNIT_TENDENCY.value_at(
            absolute_position
        )
        weight_curve_per_loudspeaker = self._make_weight_curve_for_each_loudspeaker(
            family_of_pitch_curves, average_duration_for_one_unit
        )
        for (
            loudspeaker_id,
            simultaneous_event,
        ) in loudspeaker_to_simultaneous_event.items():
            average_duration_for_one_unit_for_loudspeaker = ot3_constants.drone.AVERAGE_DURATION_FOR_ONE_UNIT_TENDENCY.value_at(
                absolute_position
            )
            attack_release_envelope = self._make_attack_release_envelope(
                family_of_pitch_curves, absolute_position
            )
            weight_curve = weight_curve_per_loudspeaker[loudspeaker_id]
            random_seed_for_brownian_rhythm = self.loudspeaker_to_random_seed_for_brownian_rhythm[
                loudspeaker_id
            ]

            populate_weight = ot3_constants.drone.ABSOLUTE_WEIGHT_TENDENCY.value_at(
                absolute_position
            )
            self._convert_family(
                loudspeaker_id,
                average_duration_for_one_unit_for_loudspeaker,
                filtered_family_of_pitch_curves,
                simultaneous_event,
                weight_curve,
                attack_release_envelope,
                random_seed_for_brownian_rhythm,
                populate_weight,
                absolute_position,
            )

    def _convert_simple_event_for_each_loudspeaker(
        self,
        simple_event: events.basic.SimpleEvent,
        loudspeaker_to_simultaneous_event: typing.Dict[
            str,
            events.basic.SimultaneousEvent[
                events.basic.SequentialEvent[
                    typing.Union[events.music.NoteLike, events.basic.SimpleEvent]
                ]
            ],
        ],
    ):
        for simultaneous_event in loudspeaker_to_simultaneous_event.values():
            for sequential_event in simultaneous_event:
                sequential_event.append(events.basic.SimpleEvent(simple_event.duration))

    def convert(
        self,
        families_pitch: events.basic.SequentialEvent[
            typing.Union[events.families.FamilyOfPitchCurves, events.basic.SimpleEvent]
        ],
    ) -> typing.Dict[
        str,
        events.basic.SimultaneousEvent[
            events.basic.SequentialEvent[
                typing.Union[events.music.NoteLike, events.basic.SimpleEvent]
            ]
        ],
    ]:
        loudspeaker_to_simultaneous_event = {
            loudspeaker_id: events.basic.SimultaneousEvent(
                [events.basic.SequentialEvent([]) for _ in range(2)]
            )
            for loudspeaker_id in ot3_constants.loudspeakers.LOUDSPEAKERS
        }

        duration_of_families_pitch = families_pitch.duration

        for absolute_time, family_of_pitch_curves_or_simple_event in zip(
            families_pitch.absolute_times, families_pitch
        ):
            if isinstance(
                family_of_pitch_curves_or_simple_event, events.basic.SimpleEvent
            ):
                self._convert_simple_event_for_each_loudspeaker(
                    family_of_pitch_curves_or_simple_event,
                    loudspeaker_to_simultaneous_event,
                )
            else:
                self._convert_family_for_each_loudspeaker(
                    family_of_pitch_curves_or_simple_event,
                    loudspeaker_to_simultaneous_event,
                    absolute_time,
                    duration_of_families_pitch,
                )

        return loudspeaker_to_simultaneous_event
