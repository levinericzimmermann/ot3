import functools
import operator
import typing

import expenvelope
import mido

from mutwo.converters.frontends import midi
from mutwo.converters import symmetrical
from mutwo.events import abc
from mutwo import parameters
from mutwo import utilities


class OT3InstrumentEventToMidiFileConverter(midi.MidiFileConverter):
    _shall_apply_tempo_coverter = True
    _tempo_converter = symmetrical.tempos.TempoConverter(
        # expenvelope.Envelope.from_levels_and_durations(levels=[7.5, 7.5], durations=[1])
        expenvelope.Envelope.from_levels_and_durations(levels=[30, 30], durations=[1])
    )

    def __init__(
        self,
        name: str,
        midi_file_type: int = 1,
        min_velocity=0,
        max_velocity=127,
        apply_extrema: bool = False,
    ):
        self._min_velocity = min_velocity
        self._max_velocity = max_velocity
        self._apply_extrema = apply_extrema
        super().__init__(
            path=f"builds/soundfiles/{name}.mid", midi_file_type=midi_file_type,
        )

    def _apply_tempo_coverter(self, event_to_convert: abc.Event) -> abc.Event:
        if self._shall_apply_tempo_coverter:
            return self._tempo_converter.convert(event_to_convert)
        else:
            return event_to_convert

    def convert(self, event_to_convert: abc.Event) -> abc.Event:
        volumes = event_to_convert.get_parameter("volume")
        while hasattr(volumes[0], "__iter__"):
            volumes = functools.reduce(operator.add, volumes)
        velocities = tuple(
            volume.midi_velocity for volume in volumes if volume
        )
        self._min_velocity_of_event = min(velocities)
        self._max_velocity_of_event = max(velocities)

        if self._min_velocity_of_event == self._max_velocity_of_event:
            self._max_velocity_of_event += 1
        return super().convert(self._apply_tempo_coverter(event_to_convert))

    def _note_information_to_midi_messages(
        self,
        absolute_tick_start: int,
        absolute_tick_end: int,
        velocity: int,
        pitch: parameters.abc.Pitch,
        available_midi_channels_cycle: typing.Iterator,
    ) -> typing.Tuple[mido.Message, ...]:
        if self._apply_extrema:
            min_vel_ev, max_vel_ev = self._min_velocity_of_event, self._max_velocity_of_event
        else:
            min_vel_ev, max_vel_ev = (0, 127)
        velocity = int(
            utilities.tools.scale(
                velocity, min_vel_ev, max_vel_ev, self._min_velocity, self._max_velocity
            )
        )
        return super()._note_information_to_midi_messages(
            absolute_tick_start,
            absolute_tick_end,
            velocity,
            pitch,
            available_midi_channels_cycle,
        )


class OT3InstrumentSimulationEventToMidiFileConverter(
    OT3InstrumentEventToMidiFileConverter
):
    def __init__(self, name: str, midi_file_type: int = 1):
        super().__init__(name, midi_file_type, 22, 48)


class DroneEventToMidiFileConverter(OT3InstrumentEventToMidiFileConverter):
    def __init__(self):
        super().__init__(
            path="builds/drone.mid", midi_file_type=1,  # polyphon instruments
        )


class CommonHarmonicEventToMidiFileConverter(OT3InstrumentEventToMidiFileConverter):
    def __init__(self, name: str):
        super().__init__(
            path=f"builds/common_harmonics_{name}.mid",
            midi_file_type=1,  # polyphon instruments
        )
