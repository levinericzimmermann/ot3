import typing

import abjad

from mutwo.converters.frontends import abjad_process_container_routines
from mutwo import events

from ot3.constants import instruments


class InstrumentMixin(abjad_process_container_routines.ProcessAbjadContainerRoutine):
    def __init__(
        self, instrument_id: str, accidental_style: typing.Optional[str] = None
    ):
        self._add_instrument_name = abjad_process_container_routines.AddInstrumentName(
            lambda _: instruments.INSTRUMENT_ID_TO_LONG_INSTRUMENT_NAME[instrument_id],
            lambda _: instruments.INSTRUMENT_ID_TO_SHORT_INSTRUMENT_NAME[instrument_id],
        )
        if accidental_style:
            self._add_accidental_style = (
                abjad_process_container_routines.AddAccidentalStyle(accidental_style)
            )
        else:
            self._add_accidental_style = None

    def __call__(
        self,
        complex_event_to_convert: events.abc.ComplexEvent,
        container_to_process: abjad.Container,
    ):
        self._add_instrument_name(complex_event_to_convert, container_to_process)
        if self._add_accidental_style:
            for sub_event, sub_container in zip(
                complex_event_to_convert, container_to_process
            ):
                self._add_accidental_style(sub_event, sub_container)


class SaxophoneMixin(InstrumentMixin):
    def __init__(self):
        instrument_id = instruments.ID_SAXOPHONE
        self._instrument_id = instrument_id
        super().__init__(
            instrument_id,
            "dodecaphonic",
        )

    def __call__(
        self,
        complex_event_to_convert: events.abc.ComplexEvent,
        container_to_process: abjad.Container,
    ):
        super().__call__(complex_event_to_convert, container_to_process)
        abjad.attach(abjad.Clef("treble"), abjad.get.leaf(container_to_process[0], 0))


class ViolinMixin(InstrumentMixin):
    def __init__(self):
        instrument_id = instruments.ID_VIOLIN
        self._instrument_id = instrument_id
        super().__init__(
            instrument_id,
            "dodecaphonic",
        )

    def __call__(
        self,
        complex_event_to_convert: events.abc.ComplexEvent,
        container_to_process: abjad.Container,
    ):
        super().__call__(complex_event_to_convert, container_to_process)
        abjad.attach(abjad.Clef("treble"), abjad.get.leaf(container_to_process[0], 0))


class DroneMixin(InstrumentMixin):
    _instrument_id = instruments.ID_DRONE

    def __init__(self):
        super().__init__(instruments.ID_DRONE, "dodecaphonic")

    def __call__(
        self,
        complex_event_to_convert: events.abc.ComplexEvent,
        container_to_process: abjad.Container,
    ):
        super().__call__(complex_event_to_convert, container_to_process)
        # attach drone clef
        abjad.attach(abjad.Clef("treble"), abjad.get.leaf(container_to_process[0], 0))

        first_leaf = abjad.get.leaf(container_to_process, 0)
        abjad.attach(abjad.BeforeGraceContainer([]), first_leaf)


class TicksMixin(abjad_process_container_routines.ProcessAbjadContainerRoutine):
    def __call__(
        self,
        complex_event_to_convert: events.abc.ComplexEvent,
        container_to_process: abjad.Container,
    ):
        first_leaf = abjad.get.leaf(container_to_process, 0)
        abjad.attach(
            abjad.LilyPondLiteral(r"\stopStaff"),
            first_leaf,
        )
        abjad.attach(
            abjad.LilyPondLiteral(r"\override Staff.TimeSignature.transparent = ##t"),
            first_leaf,
        )
        abjad.attach(
            abjad.LilyPondLiteral(r"\override Staff.BarNumber.transparent = ##t"),
            first_leaf,
        )
        abjad.attach(
            abjad.LilyPondLiteral(r"\override Staff.BarLine.transparent = ##t"),
            first_leaf,
        )
        abjad.attach(
            abjad.LilyPondLiteral(r"\override Staff.Clef.transparent = ##t"), first_leaf
        )
        abjad.attach(
            abjad.LilyPondLiteral(r"\override Staff.GridLine.transparent = ##t"),
            first_leaf,
        )
        # abjad.attach(
        #     abjad.LilyPondLiteral(r"\override NoteHead.transparent = ##t"), first_leaf
        # )
        abjad.attach(
            abjad.LilyPondLiteral(r"\override Stem.transparent = ##t"), first_leaf
        )
        abjad.attach(
            abjad.LilyPondLiteral(r"\override Beam.transparent = ##t"), first_leaf
        )
        abjad.attach(
            abjad.LilyPondLiteral(
                r"\override Staff.StaffSymbol.line-count = #0", format_slot="before"
            ),
            first_leaf,
        )


class PostProcessIslandTimeBracket(
    abjad_process_container_routines.ProcessAbjadContainerRoutine
):
    def __call__(
        self,
        complex_event_to_convert: events.abc.ComplexEvent,
        container_to_process: abjad.Container,
    ):
        for staff_group in container_to_process:
            for staff in staff_group:
                first_leaf = abjad.get.leaf(staff, 0)
                abjad.attach(
                    abjad.LilyPondLiteral(
                        "\\set Score.proportionalNotationDuration = #(ly:make-moment"
                        " 1/8)"
                    ),
                    first_leaf,
                )

                last_leaf = abjad.get.leaf(staff, -1)

                abjad.attach(abjad.LilyPondLiteral("\\cadenzaOn"), first_leaf)
                abjad.attach(
                    abjad.LilyPondLiteral("\\omit Staff.TimeSignature"), first_leaf
                )

                try:
                    abjad.attach(
                        abjad.BarLine("|.", format_slot="absolute_after"), last_leaf
                    )
                except Exception:
                    pass
                abjad.attach(
                    abjad.LilyPondLiteral(
                        r"\undo \hide Staff.BarLine", format_slot="absolute_after"
                    ),
                    last_leaf,
                )


class PostProcessWestminsterTimeBracket(
    abjad_process_container_routines.ProcessAbjadContainerRoutine
):
    def __init__(self, render_video: bool = False):
        self._render_video = render_video

    def __call__(
        self,
        complex_event_to_convert: events.abc.ComplexEvent,
        container_to_process: abjad.Container,
    ):
        if self._render_video:
            make_moment_duration = 8
        else:
            make_moment_duration = 32
        for staff_group in container_to_process:
            for staff in staff_group:
                first_leaf = abjad.get.leaf(staff, 0)
                abjad.attach(
                    abjad.LilyPondLiteral(
                        "\\set Score.proportionalNotationDuration = #(ly:make-moment"
                        " 1/{})".format(make_moment_duration)
                    ),
                    first_leaf,
                )
                abjad.attach(
                    abjad.LilyPondLiteral(
                        "\\override Staff.TimeSignature.style = #'single-digit"
                    ),
                    first_leaf,
                )
                abjad.attach(
                    abjad.LilyPondLiteral(
                        "\\override SpacingSpanner.base-shortest-duration = #(ly:make-moment 1/{})".format(
                            make_moment_duration
                        )
                    ),
                    first_leaf,
                )

                last_leaf = abjad.get.leaf(staff, -1)

                try:
                    abjad.attach(
                        abjad.BarLine("|.", format_slot="absolute_after"), last_leaf
                    )
                except Exception:
                    pass
