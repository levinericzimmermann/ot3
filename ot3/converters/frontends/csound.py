from mutwo.converters.frontends import csound
from mutwo import events
from mutwo import parameters
from mutwo import utilities

from ot3.converters.frontends import csound_constants


class DroneSimultaneousEventToSoundFileConverter(csound.CsoundConverter):
    def __init__(self):
        csound_score_converter = csound.CsoundScoreConverter(
            "{}/drone.sco".format(csound_constants.FILES_PATH),
            p4=lambda note_like: note_like.pitch_or_pitches[0].frequency,
            p5=lambda note_like: note_like.volume.amplitude,
            p6=lambda note_like: note_like.attack,
            p7=lambda note_like: note_like.sustain,
            p8=lambda note_like: note_like.release,
        )
        super().__init__(
            "builds/soundfiles/drone.wav",
            "{}/drone.orc".format(csound_constants.FILES_PATH),
            csound_score_converter,
            remove_score_file=True,
        )


class VolumeScalingCsoundScoreConverter(csound.CsoundScoreConverter):
    def __init__(self, *args, min_decibel=-30, max_decibel=0, **kwargs):
        self._min_decibel = min_decibel
        self._max_decibel = max_decibel
        super().__init__(*args, **kwargs)

    def _convert_simple_event(
        self,
        event_to_convert: events.basic.SimpleEvent,
        absolute_entry_delay: parameters.abc.DurationType,
    ):
        if hasattr(event_to_convert, "volume"):
            event_to_convert.volume = parameters.volumes.DecibelVolume(
                utilities.tools.scale(
                    event_to_convert.volume.decibel,
                    self._min_decibel_in_event,
                    self._max_decibel_in_event,
                    self._min_decibel,
                    self._max_decibel,
                )
            )
        return super()._convert_simple_event(event_to_convert, absolute_entry_delay)

    def convert(self, event_to_convert: events.abc.Event):
        decibels = tuple(
            map(
                lambda v: v.decibel,
                filter(
                    lambda volume: volume is not None,
                    event_to_convert.get_parameter("volume", flat=True),
                ),
            )
        )
        self._min_decibel_in_event, self._max_decibel_in_event = (
            min(decibels),
            max(decibels),
        )
        return super().convert(event_to_convert)


class SineTonesToSoundFileConverter(csound.CsoundConverter):
    def __init__(
        self, instrument_id: str,
    ):
        csound_score_converter = csound.CsoundScoreConverter(
            f"{csound_constants.FILES_PATH}/{instrument_id}.sco",
            p4=SineTonesToSoundFileConverter._get_pitch,
            p5=lambda note_like: note_like.volume.amplitude,
        )
        super().__init__(
            f"builds/soundfiles/{instrument_id}.wav",
            "{}/sine.orc".format(csound_constants.FILES_PATH),
            csound_score_converter,
            remove_score_file=True,
        )

    @staticmethod
    def _get_pitch(note_like):
        pitch_or_pitches = note_like.pitch_or_pitches
        if len(pitch_or_pitches) > 0:
            return note_like.pitch_or_pitches[0].frequency


class SaturationSineTonesToSoundFileConverter(csound.CsoundConverter):
    def __init__(self, instrument_id: str, min_decibel=-20, max_decibel=-6):
        csound_score_converter = VolumeScalingCsoundScoreConverter(
            f"{csound_constants.FILES_PATH}/{instrument_id}.sco",
            min_decibel=min_decibel,
            max_decibel=max_decibel,
            p4=SineTonesToSoundFileConverter._get_pitch,
            p5=lambda note_like: note_like.volume.amplitude,
            p6=lambda note_like: note_like.min_modulation,
            p7=lambda note_like: note_like.glissando_factor,
            p8=lambda note_like: note_like.glissando_duration,
        )
        super().__init__(
            f"builds/soundfiles/{instrument_id}.wav",
            f"{csound_constants.FILES_PATH}/sine_saturation.orc",
            csound_score_converter,
            remove_score_file=True,
        )
