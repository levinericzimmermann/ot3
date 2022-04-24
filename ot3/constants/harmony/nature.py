import typing

from mutwo import parameters


class Pendulum(object):
    def __init__(
        self,
        center: parameters.pitches.JustIntonationPitch,
        left_side: typing.Sequence[parameters.pitches.JustIntonationPitch],
        right_side: typing.Sequence[parameters.pitches.JustIntonationPitch],
    ):
        self.center = center
        self.left_side = left_side
        self.right_side = right_side
        self._line = (
            (self.center,)
            + tuple(self.left_side)
            + tuple(reversed(self.right_side))[1:]
        )

    def __repr__(self) -> str:
        return f"Pendulum({repr(self.center)})"

    def __getitem__(self, index: int):
        return self._line[index]

    def get_side(
        self, direction: bool
    ) -> typing.Tuple[parameters.pitches.JustIntonationPitch, ...]:
        if direction:
            return self.left_side
        return self.right_side


RootPitches = typing.Tuple[parameters.pitches.JustIntonationPitch, ...]
ConnectionPitches = typing.Tuple[parameters.pitches.JustIntonationPitch, ...]
Duration = parameters.abc.DurationType


class Wind(object):
    def __init__(
        self,
        duration: parameters.abc.DurationType,
        duration_per_root: parameters.abc.DurationType,
        strength: int,
        direction: bool,
    ):
        self._duration = duration
        self._duration_per_root = duration_per_root
        self._strength = strength
        self._direction = direction

    def move(
        self, pendulum: Pendulum
    ) -> typing.Tuple[RootPitches, ConnectionPitches, Duration]:
        root_pitches = [pendulum.center]
        connection_pitches = []
        duration = self._duration_per_root
        current_position = 0
        current_direction = self._direction
        while duration < self._duration:
            next_position = current_position + (-1, 1)[current_direction]
            next_pitch = pendulum[next_position]

            if next_position % 2 == 0:
                root_pitches.append(next_pitch)
            else:
                connection_pitches.append(next_pitch)

            if abs(next_position) >= self._strength:
                current_direction = not current_direction

            current_position = next_position
            duration += self._duration_per_root

        if current_position % 2 != 0:
            root_pitches.append(root_pitches[-1])
            duration += self._duration_per_root

        if not connection_pitches:
            connection_pitches.append(pendulum.get_side(self._direction)[0])
            root_pitches.append(pendulum.center)
            duration += self._duration_per_root

        assert len(root_pitches) == len(connection_pitches) + 1

        return root_pitches, connection_pitches, duration


PENDULUM0 = Pendulum(
    parameters.pitches.JustIntonationPitch("1/1"),
    tuple(
        parameters.pitches.JustIntonationPitch(ratio)
        for ratio in "4/3 3/2 12/7 8/7 10/7 5/4 35/32".split(" ")
    ),
    tuple(
        parameters.pitches.JustIntonationPitch(ratio)
        for ratio in "3/2 4/3 7/6 7/4 21/16 7/4 35/32".split(" ")
    ),
)


PENDULUM1 = Pendulum(
    parameters.pitches.JustIntonationPitch("35/32"),
    tuple(
        parameters.pitches.JustIntonationPitch(ratio)
        for ratio in "5/4 10/7 8/7 12/7 3/2 4/3 1/1".split(" ")
    ),
    tuple(
        parameters.pitches.JustIntonationPitch(ratio)
        for ratio in "7/4 21/16 7/4 7/6 4/3 3/2 1/1".split(" ")
    ),
)
