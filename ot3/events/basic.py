import typing

from mutwo.events import abc
from mutwo.events import basic


T = typing.TypeVar("T", bound=abc.Event)


class SequentialEventWithTempo(basic.SequentialEvent, typing.Generic[T]):
    _class_specific_side_attributes = (
        "tempo",
    ) + basic.SequentialEvent._class_specific_side_attributes

    def __init__(self, events: typing.Sequence[abc.Event], tempo: float):
        super().__init__(events)
        self.tempo = tempo
