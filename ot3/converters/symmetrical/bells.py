import abc
import typing

import expenvelope
import numpy as np

from mutwo import converters
from mutwo import events
from mutwo import generators
from mutwo import parameters
from mutwo import utilities

from ot3 import constants as ot3_constants
from ot3 import converters as ot3_converters
from ot3 import utilities as ot3_utilities


class Cloud(events.basic.SimpleEvent):
    def __init__(
        self,
        start_time: parameters.abc.DurationType,
        average_note_duration: parameters.abc.DurationType,
        duration: parameters.abc.DurationType,
    ):
        super().__init__(duration)
        self.average_note_duration = average_note_duration
        self.start_time = start_time


class CloudToSequentialEventConverter(converters.abc.Converter):
    def __init__(
        self, family_of_pitch_curves: events.families.FamilyOfPitchCurves,
    ):
        self._family_of_pitch_curves = family_of_pitch_curves

    def convert(
        self, cloud_to_convert: Cloud
    ) -> events.basic.SequentialEvent[events.music.NoteLike]:
        raise NotImplementedError


class StochasticCloudToSequentialEventConverter(CloudToSequentialEventConverter):
    def __init__(
        self,
        family_of_pitch_curves: events.families.FamilyOfPitchCurves,
        seed: int = 12345,
    ):
        super().__init__(family_of_pitch_curves)
        self._seed = seed
        self._random = np.random.default_rng(seed=seed)
        self._assigner = converters.symmetrical.families.AssignCurveAndWeightPairsOnEventsConverter(
            family_of_pitch_curves,
        )
        self._picker = ot3_converters.symmetrical.families.PickBellPitchesFromCurveAndWeightPairsConverter(
            seed=seed
        )

    def _add_accelerando_and_rilatando_to_rhythm(
        self,
        rhythm_to_process: typing.Tuple[float, ...],
        absolute_entry_delay: parameters.abc.DurationType,
    ) -> typing.Tuple[float, ...]:
        factor = self._get_accelerando_and_rilatando_factor(absolute_entry_delay)
        if factor > 0:
            areas = generators.toussaint.euclidean(len(rhythm_to_process), 4)
            indices_per_area = tuple(
                tuple(map(lambda index: index + position, range(n_items)))
                for n_items, position in zip(
                    areas, utilities.tools.accumulate_from_zero(areas)
                )
            )

            processed_rhythm = list(rhythm_to_process)

            for indices_to_spend_to, indices_to_steal_from in (
                indices_per_area[:2],
                tuple(
                    tuple(reversed(indices))
                    for indices in (indices_per_area[3], indices_per_area[2])
                ),
            ):
                n_indices_to_spend_to = len(indices_to_spend_to)
                n_indices_to_steal_from = len(indices_to_steal_from)
                max_length = min((n_indices_to_spend_to, n_indices_to_steal_from))
                factor_per_index = np.linspace(0, factor, max_length + 1, dtype=float)[
                    1:
                ]
                for exchange_factor, index_to_spend_to, index_to_steal_from in zip(
                    factor_per_index,
                    reversed(indices_to_spend_to),
                    indices_to_steal_from,
                ):
                    steal_duration = (
                        processed_rhythm[index_to_steal_from] * exchange_factor
                    )
                    processed_rhythm[index_to_spend_to] += steal_duration
                    processed_rhythm[index_to_steal_from] -= steal_duration

                # all_used_indices = indices_to_spend_to + indices_to_steal_from
                # processed_rhythm[min(all_used_indices) : max(all_used_indices)] = sorted(
                #     processed_rhythm[min(all_used_indices) : max(all_used_indices)],
                #     reverse=reverse,
                # )

            return processed_rhythm

        else:
            return tuple(rhythm_to_process)

    @abc.abstractmethod
    def _make_rhythm(
        self, cloud_to_convert: Cloud
    ) -> typing.Sequence[parameters.abc.DurationType]:
        raise NotImplementedError

    @abc.abstractmethod
    def _get_accelerando_and_rilatando_factor(
        self, absolute_entry_delay: parameters.abc.DurationType
    ) -> float:
        raise NotImplementedError

    def convert(
        self, cloud_to_convert: Cloud
    ) -> events.basic.SequentialEvent[events.music.NoteLike]:
        rhythm = self._make_rhythm(cloud_to_convert)
        rhythm = self._add_accelerando_and_rilatando_to_rhythm(
            rhythm, cloud_to_convert.start_time
        )
        sequential_event = events.basic.SequentialEvent([])
        for duration in rhythm:
            note_like = events.music.NoteLike(
                pitch_or_pitches=[],
                duration=duration,
                volume=parameters.volumes.DecibelVolume(-30),
            )
            sequential_event.append(note_like)

        has_delay = False
        if cloud_to_convert.start_time > 0:
            has_delay = True
            sequential_event.insert(
                0, events.basic.SimpleEvent(cloud_to_convert.start_time)
            )

        assigned_sequential_event = self._assigner.convert(sequential_event)
        picked_sequential_event = self._picker.convert(assigned_sequential_event)

        if has_delay:
            picked_sequential_event = picked_sequential_event[1:]

        return picked_sequential_event


class PeriodicStochasticCloudToSequentialEventConverter(
    StochasticCloudToSequentialEventConverter
):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._accelerando_and_rilatando_factor_choice = generators.generic.DynamicChoice(
            (0.98, 0.85, 0.75, 0.65, 0.5, 0.3, 0.1, 0),
            (
                # 0.98
                expenvelope.Envelope.from_points(
                    (0, 0.2), (0.1, 0.4), (0.4, 0.3), (0.6, 1), (0.8, 0)
                ),
                # 0.85
                expenvelope.Envelope.from_points(
                    (0, 0.4), (0.1, 0.8), (0.6, 1), (0.8, 0)
                ),
                # 0.75
                expenvelope.Envelope.from_points(
                    (0, 0.4), (0.1, 0.8), (0.6, 1), (0.8, 0)
                ),
                # 0.65
                expenvelope.Envelope.from_points(
                    (0, 0.55), (0.1, 0.3), (0.6, 0.2), (0.8, 0.4), (0.9, 0.1)
                ),
                # 0.5
                expenvelope.Envelope.from_points(
                    (0, 0.45), (0.1, 0.1), (0.6, 0), (0.8, 0.5), (0.9, 0.2), (1, 0)
                ),
                # 0.3
                expenvelope.Envelope.from_points(
                    (0, 0.25), (0.1, 0), (0.75, 0), (0.8, 0.2), (1, 0.4)
                ),
                # 0.1
                expenvelope.Envelope.from_points(
                    (0, 0), (0.75, 0), (0.8, 0.2), (1, 0.9)
                ),
                # 0
                expenvelope.Envelope.from_points(
                    (0, 0), (0.79, 0), (0.8, 0.1), (1, 1.5)
                ),
            ),
        )

    def _get_accelerando_and_rilatando_factor(
        self, absolute_entry_delay: parameters.abc.DurationType
    ) -> float:
        absolute_position = (
            absolute_entry_delay / ot3_constants.families_pitch.FAMILIES_PITCH.duration
        )
        return self._accelerando_and_rilatando_factor_choice.gamble_at(
            absolute_position
        )

    def _make_rhythm(
        self, cloud_to_convert: Cloud
    ) -> typing.Sequence[parameters.abc.DurationType]:
        duration = cloud_to_convert.duration
        expected_average_note_duration = cloud_to_convert.average_note_duration
        n_times = int(duration / expected_average_note_duration)
        real_average_note_duration = duration / n_times
        return [real_average_note_duration for _ in range(n_times)]


class GaussianStochasicCloudToSequentialEventConverter(
    PeriodicStochasticCloudToSequentialEventConverter
):
    def _make_rhythm(
        self, cloud_to_convert: Cloud
    ) -> typing.Sequence[parameters.abc.DurationType]:
        duration = cloud_to_convert.duration
        expected_average_note_duration = cloud_to_convert.average_note_duration
        n_times = int(duration / expected_average_note_duration)
        real_average_note_duration = duration / n_times
        rhythm = [real_average_note_duration for _ in range(n_times)]
        factor_per_note = [self._random.normal(1, scale=0.2) for _ in rhythm]
        rhythm = [
            note_duration * factor
            for note_duration, factor in zip(rhythm, factor_per_note)
        ]
        rhythm = [
            0.01 if note_duration <= 0 else note_duration for note_duration in rhythm
        ]
        difference_to_expected_duration = duration - sum(rhythm)
        difference_to_expected_duration_per_note = (
            difference_to_expected_duration / n_times
        )
        rhythm = [
            note_duration + difference_to_expected_duration_per_note
            for note_duration in rhythm
        ]
        return rhythm


class ArpeggiBasedGaussianStochasicCloudToSequentialEventConverter(
    GaussianStochasicCloudToSequentialEventConverter
):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._picker = ot3_converters.symmetrical.families.PickBellArpeggiFromCurveAndWeightPairsConverter(
            seed=13
        )


class ArpeggiBasedPeriodicStochasicCloudToSequentialEventConverter(
    PeriodicStochasticCloudToSequentialEventConverter
):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._picker = ot3_converters.symmetrical.families.PickBellArpeggiFromCurveAndWeightPairsConverter(
            seed=15
        )


class ChordBasedGaussianStochasicCloudToSequentialEventConverter(
    GaussianStochasicCloudToSequentialEventConverter
):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._picker = ot3_converters.symmetrical.families.PickBellChordsFromCurveAndWeightPairsConverter(
            seed=10
        )


class BrownianStochasticCloudToSequentialEventConverter(
    StochasticCloudToSequentialEventConverter
):
    def _get_accelerando_and_rilatando_factor(
        self, absolute_entry_delay: parameters.abc.DurationType
    ) -> float:
        return 0.5

    def _make_rhythm(
        self, cloud_to_convert: Cloud
    ) -> typing.Sequence[parameters.abc.DurationType]:
        return ot3_utilities.tools.make_brownian_rhythm(
            cloud_to_convert.duration,
            cloud_to_convert.average_note_duration,
            self._seed,
        )


class FamilyOfPitchCurvesToBellConverter(converters.abc.Converter):
    def __init__(self, seed: int):
        self._seed = seed

    def _initialise_cloud_to_sequential_event_converters(
        self, family_of_pitch_curves_to_convert: events.families.FamilyOfPitchCurves
    ):
        self._cloud_to_sequential_event_converters = generators.generic.DynamicChoice(
            (
                PeriodicStochasticCloudToSequentialEventConverter(
                    family_of_pitch_curves_to_convert, self._seed
                ),
                GaussianStochasicCloudToSequentialEventConverter(
                    family_of_pitch_curves_to_convert, self._seed + 10
                ),
                ChordBasedGaussianStochasicCloudToSequentialEventConverter(
                    family_of_pitch_curves_to_convert, self._seed + 20
                ),
                ArpeggiBasedGaussianStochasicCloudToSequentialEventConverter(
                    family_of_pitch_curves_to_convert, self._seed + 30
                ),
            ),
            (
                # periodic random
                expenvelope.Envelope.from_points(
                    (0, 0), (0.05, 0), (0.2, 0.5), (0.6, 0), (0.8, 0), (1, 0.2)
                ),
                # gaussian random
                expenvelope.Envelope.from_points(
                    (0, 0), (0.1, 0), (0.3, 0.5), (0.6, 0.75), (0.7, 0.65), (1, 0)
                ),
                # gaussian chords
                expenvelope.Envelope.from_points(
                    (0, 0.7), (0.28, 0), (0.5, 0), (0.8, 0), (1, 1)
                ),
                # gaussian arpeggi
                expenvelope.Envelope.from_points(
                    (0, 0), (0.4, 0), (0.6, 0.65), (0.75, 0.7), (1, 0)
                ),
            ),
        )

    def _add_rest(
        self,
        sequential_event_to_add_rest_to: events.basic.SequentialEvent,
        absolute_position: float,
    ):
        rest_duration = ot3_constants.clouds.REST_DURATION_TENDENCY.value_at(
            absolute_position
        )
        sequential_event_to_add_rest_to.append(events.basic.SimpleEvent(rest_duration))

    def _get_cloud_to_sequential_event_converter(
        self, absolute_position: float
    ) -> CloudToSequentialEventConverter:
        return self._cloud_to_sequential_event_converters.gamble_at(absolute_position)

    def _add_cloud(
        self,
        sequential_event_to_add_cloud_to: events.basic.SequentialEvent,
        absolute_position: float,
    ):
        cloud_duration = ot3_constants.clouds.DURATION_TENDENCY.value_at(
            absolute_position
        )
        average_note_duration = ot3_constants.clouds.NOTE_DURATION_TENDENCY.value_at(
            absolute_position
        )
        cloud = Cloud(
            sequential_event_to_add_cloud_to.duration,
            average_note_duration,
            cloud_duration,
        )
        converter = self._get_cloud_to_sequential_event_converter(absolute_position)
        converted_cloud = converter.convert(cloud)
        sequential_event_to_add_cloud_to.extend(converted_cloud)

    def convert(
        self, family_of_pitch_curves_to_convert: events.families.FamilyOfPitchCurves
    ) -> events.basic.SequentialEvent:
        self._initialise_cloud_to_sequential_event_converters(
            family_of_pitch_curves_to_convert
        )
        sequential_event = events.basic.SequentialEvent([])
        counter = 0
        while (
            sequential_event.duration
            < ot3_constants.families_pitch.FAMILIES_PITCH.duration
        ):
            absolute_position = (
                sequential_event.duration
                / ot3_constants.families_pitch.FAMILIES_PITCH.duration
            )
            if counter % 2 == 0:
                self._add_rest(sequential_event, absolute_position)
            else:
                self._add_cloud(
                    sequential_event, absolute_position,
                )

            counter += 1

        return sequential_event
