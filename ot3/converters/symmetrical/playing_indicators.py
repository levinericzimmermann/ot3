import copy
import itertools
import random

from mutwo.converters import symmetrical
from mutwo import events
from mutwo import parameters

from ot3.parameters import playing_indicators as ot3_playing_indicators


class ExplicitFermataConverter(
    symmetrical.playing_indicators.PlayingIndicatorConverter
):
    def _apply_playing_indicator(
        self,
        simple_event_to_convert: events.basic.SimpleEvent,
        playing_indicators: parameters.playing_indicators.PlayingIndicatorCollection,
    ) -> events.basic.SequentialEvent[events.basic.SimpleEvent]:
        try:
            explicit_fermata = playing_indicators.explicit_fermata
        except AttributeError:
            explicit_fermata = ot3_playing_indicators.ExplicitFermata()

        simple_event_to_convert = copy.deepcopy(simple_event_to_convert)
        if explicit_fermata.is_active:
            simple_event_to_convert.duration += random.uniform(
                *explicit_fermata.waiting_range
            )

        return events.basic.SequentialEvent([simple_event_to_convert])


class BowNoiseConverter(symmetrical.playing_indicators.PlayingIndicatorConverter):
    bow_noise_cycle = itertools.cycle((4, 7, 5, 8))

    def _apply_playing_indicator(
        self,
        simple_event_to_convert: events.basic.SimpleEvent,
        playing_indicators: parameters.playing_indicators.PlayingIndicatorCollection,
    ) -> events.basic.SequentialEvent[events.basic.SimpleEvent]:
        try:
            bow_noise = playing_indicators.bow_noise
        except AttributeError:
            bow_noise = parameters.abc.ExplicitPlayingIndicator()

        simple_event_to_convert = copy.deepcopy(simple_event_to_convert)
        if bow_noise.is_active:
            simple_event_to_convert.pitch_or_pitches = [
                parameters.pitches.MidiPitch(next(self.bow_noise_cycle))
            ]

        return events.basic.SequentialEvent([simple_event_to_convert])


class HarmonicGlissandoConverter(
    symmetrical.playing_indicators.PlayingIndicatorConverter
):
    harmonic_glissando_cycle = itertools.cycle((14, 12, 14, 14, 12))

    def _apply_playing_indicator(
        self,
        simple_event_to_convert: events.basic.SimpleEvent,
        playing_indicators: parameters.playing_indicators.PlayingIndicatorCollection,
    ) -> events.basic.SequentialEvent[events.basic.SimpleEvent]:
        try:
            harmonic_glissando = playing_indicators.harmonic_glissando
        except AttributeError:
            harmonic_glissando = parameters.abc.ExplicitPlayingIndicator()

        simple_event_to_convert = copy.deepcopy(simple_event_to_convert)
        if harmonic_glissando.is_active:
            simple_event_to_convert.pitch_or_pitches = [
                parameters.pitches.MidiPitch(next(self.harmonic_glissando_cycle))
            ]

        return events.basic.SequentialEvent([simple_event_to_convert])


class TeethOnReedConverter(symmetrical.playing_indicators.PlayingIndicatorConverter):
    def _apply_playing_indicator(
        self,
        simple_event_to_convert: events.basic.SimpleEvent,
        playing_indicators: parameters.playing_indicators.PlayingIndicatorCollection,
    ) -> events.basic.SequentialEvent[events.basic.SimpleEvent]:
        try:
            teeth_on_reed = playing_indicators.teeth_on_reed
        except AttributeError:
            teeth_on_reed = parameters.abc.ExplicitPlayingIndicator()

        simple_event_to_convert = copy.deepcopy(simple_event_to_convert)
        if teeth_on_reed.is_active:
            simple_event_to_convert.pitch_or_pitches = [
                parameters.pitches.MidiPitch(13)
            ]

        return events.basic.SequentialEvent([simple_event_to_convert])
