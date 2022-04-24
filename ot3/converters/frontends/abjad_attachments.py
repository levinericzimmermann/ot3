import typing

import abjad  # type: ignore

from mutwo.converters.frontends import abjad_attachments
from mutwo.converters.frontends import abjad_constants as mutwo_abjad_constants
from mutwo import parameters

from ot3.parameters import notation_indicators
from ot3.parameters import playing_indicators


class ExplicitFermata(
    playing_indicators.ExplicitFermata, abjad_attachments.BangFirstAttachment
):
    def process_leaf(self, leaf: abjad.Leaf) -> abjad.Leaf:
        abjad.attach(
            abjad.Markup(
                contents="\\small {}-{} s".format(*self.waiting_range), direction="^"
            ),
            leaf,
        )
        abjad.attach(
            abjad.Fermata(self.fermata_type), leaf,
        )
        return leaf


class EmptyGraceContainer(
    parameters.abc.ExplicitPlayingIndicator, abjad_attachments.BangFirstAttachment
):
    def process_leaf(self, leaf: abjad.Leaf) -> abjad.Leaf:
        grace_container = abjad.BeforeGraceContainer(
            [abjad.Skip(abjad.Duration((1, 256)))]
        )
        abjad.attach(
            grace_container, leaf,
        )
        return leaf


class Fingering(playing_indicators.Fingering, abjad_attachments.BangFirstAttachment):
    fingering_size = 0.7

    @staticmethod
    def _tuple_to_scheme_list(tuple_to_convert: typing.Tuple[str, ...]) -> str:
        return f"({' '.join(tuple_to_convert)})"

    def _get_markup_content(self) -> str:
        # \\override #'(graphical . #f)
        return f"""
\\override #'(size . {self.fingering_size})
{{
    \\woodwind-diagram
    #'alto-saxophone
    #'((cc . {self._tuple_to_scheme_list(self.cc)})
       (lh . {self._tuple_to_scheme_list(self.lh)})
       (rh . {self._tuple_to_scheme_list(self.rh)}))
}}"""

    def process_leaf(self, leaf: abjad.Leaf) -> abjad.Leaf:
        fingering = abjad.LilyPondLiteral(
            f"^\\markup {self._get_markup_content()}", format_slot="after"
        )
        abjad.attach(fingering, leaf)
        return leaf


class CombinedFingerings(
    playing_indicators.CombinedFingerings, abjad_attachments.BangFirstAttachment
):
    def process_leaf(self, leaf: abjad.Leaf) -> abjad.Leaf:
        fingerings_as_abjad_attachments = tuple(
            Fingering(**fingering.get_arguments_dict()) for fingering in self.fingerings
        )
        fingerings_as_markup_contents = tuple(
            fingering._get_markup_content()
            for fingering in fingerings_as_abjad_attachments
        )
        # fingerings = '\\hspace #0.2 \\raise #5 \\smallCaps "or" \\hspace #0.2\n'.join(
        #     fingerings_as_markup_contents
        # )
        if len(self.fingerings) > 1:
            distance = -2
        else:
            distance = 0
        fingerings = f'\\hspace #-0.1 \\raise #3 \\teeny "or" \\hspace #-0.1\n'.join(
            fingerings_as_markup_contents
        )
        fingerings = f"\\line {{ \\hspace #{distance} {fingerings} }}"
        fingerings = abjad.LilyPondLiteral(
            f"^\\markup {fingerings}", format_slot="after"
        )
        abjad.attach(fingerings, leaf)
        return leaf


class BendBefore(playing_indicators.BendBefore, abjad_attachments.AbjadAttachment):
    def process_leaves(
        self, leaves: typing.Tuple[abjad.Leaf, ...], _,
    ) -> typing.Tuple[abjad.Leaf, ...]:
        processed_leaves = [abjad.mutate.copy(leaf) for leaf in leaves]

        first_leaf = processed_leaves[0]
        first_leaf.note_head._written_pitch = leaves[0].note_head._written_pitch
        abjad.attach(
            abjad.LilyPondLiteral("\\cadenzaOff", format_slot="after"), first_leaf
        )

        new_leaf = abjad.Note(
            abjad.NumberedPitch(first_leaf.written_pitch.number + self.bend_interval),
            abjad.Duration((1, 256)),
        )
        abjad.attach(abjad.Glissando(), new_leaf)

        abjad.attach(
            abjad.LilyPondLiteral(
                f"\\once \\override Glissando.minimum-length = #{self.bend_length}",
                format_slot="before",
            ),
            new_leaf,
        )
        abjad.attach(
            abjad.LilyPondLiteral(
                "\\once \\override Glissando.springs-and-rods ="
                " #ly:spanner::set-spacing-rods",
                format_slot="before",
            ),
            new_leaf,
        )
        abjad.attach(
            abjad.LilyPondLiteral(
                "\\once \\override Glissando.thickness = #3", format_slot="before",
            ),
            new_leaf,
        )
        abjad.attach(
            abjad.LilyPondLiteral("\\cadenzaOn", format_slot="before",), new_leaf,
        )
        abjad.attach(
            abjad.LilyPondLiteral("\\hideNotes", format_slot="before",), new_leaf,
        )
        abjad.attach(
            abjad.LilyPondLiteral("\\unHideNotes", format_slot="after",), new_leaf,
        )

        new_leaf_container = abjad.BeforeGraceContainer([new_leaf])

        abjad.attach(new_leaf_container, first_leaf)

        new_voice = abjad.Voice(processed_leaves)
        new_voice.consists_commands.append("Duration_line_engraver")

        return (new_voice,)


class Noise(notation_indicators.Noise, abjad_attachments.BangFirstAttachment):
    border = 0.25
    y_center = 0.5
    maxima_width = 94
    # presence_to_height = {0: 2.5, 1: 3.5, 2: 4.7}
    presence_to_height = {0: 2.5, 1: 2.5, 2: 2.5}
    presence_to_color = {0: "#white", 1: "#(x11-color 'grey75)", 2: "#black"}
    density_to_percentage_density = {0: 0.075, 1: 0.2, 2: 0.4}

    import random

    random_module = random
    random_module.seed(100)

    @staticmethod
    def _make_box(color: str, height: float, width: float, border: float) -> str:
        def _make_coordinates(a: float, b: float) -> str:
            return f"#'({a} . {b})"

        def _make_box_part(x_start: float, height: float, width: float) -> str:
            x_coordinates = _make_coordinates(x_start, x_start + width)
            halved_height = height / 2
            y_coordinates = _make_coordinates(
                Noise.y_center + halved_height, Noise.y_center - halved_height
            )
            return f"\\filled-box {x_coordinates} {y_coordinates} #1"

        lines = (
            "\\combine",
            _make_box_part(0, height, width),
            f"\\with-color {color}",
            _make_box_part(border, height - (border * 2), width - (border * 2)),
        )
        return "\n".join(lines)

    @staticmethod
    def _make_continous_noise(presence: int) -> str:
        return Noise._make_box(
            Noise.presence_to_color[presence],
            Noise.presence_to_height[presence],
            Noise.maxima_width,
            Noise.border,
        )

    @staticmethod
    def _make_discreet_noise_blueprint_box(presence: int, box_width: float) -> str:
        border = Noise.border
        height = Noise.presence_to_height[presence]
        color = Noise.presence_to_color[presence]
        box_blueprint = Noise._make_box(color, height, box_width, border)
        return box_blueprint

    @staticmethod
    def _make_discreet_noise_distances(
        density: int, width: float, box_width: float
    ) -> typing.Tuple[float, ...]:
        max_n_boxes = width / (box_width + 0.25)
        n_boxes_to_distribute = int(
            Noise.density_to_percentage_density[density] * max_n_boxes
        )
        remaining_space = width - (n_boxes_to_distribute * box_width)
        horizontal_distances = [0 for _ in range(n_boxes_to_distribute)]
        horizontal_distances_indices = list(range(len(horizontal_distances)))
        Noise.random_module.shuffle(horizontal_distances_indices)
        average_horizontal_distance = remaining_space / len(horizontal_distances)
        distance_for_pair = average_horizontal_distance * 2
        max_distance = average_horizontal_distance * 1.95
        for index0, index1 in zip(
            horizontal_distances_indices[::2], horizontal_distances_indices[1::2]
        ):
            distance0 = Noise.random_module.uniform(
                average_horizontal_distance, max_distance
            )
            distance1 = distance_for_pair - distance0
            horizontal_distances[index0] = distance0
            horizontal_distances[index1] = distance1
        return tuple(horizontal_distances)

    @staticmethod
    def _make_discreet_noise(density: int, presence: int) -> str:
        box_width = 0.9
        box_blueprint = Noise._make_discreet_noise_blueprint_box(presence, box_width)
        width = 80
        horizontal_distances = Noise._make_discreet_noise_distances(
            density, width, box_width
        )
        boxes_and_spaces = []
        for distance in horizontal_distances:
            boxes_and_spaces.append(box_blueprint)
            boxes_and_spaces.append(f"\\hspace #{distance}")
        return "\n".join(boxes_and_spaces)

    def process_leaf(self, leaf: abjad.Leaf) -> abjad.Leaf:
        if self.density == 3:
            noise_string = Noise._make_continous_noise(self.presence)
        else:
            noise_string = Noise._make_discreet_noise(self.density, self.presence)

        lilypond_literal = abjad.LilyPondLiteral(
            r"_\markup { " + noise_string + " }", "after"
        )

        abjad.attach(
            abjad.LilyPondLiteral(
                "\\override Staff.StaffSymbol.line-count = #1", format_slot="before"
            ),
            leaf,
        )
        abjad.attach(
            abjad.LilyPondLiteral("\\once \\hide Staff.Clef", format_slot="before"),
            leaf,
        )

        abjad.attach(
            lilypond_literal, leaf,
        )
        return leaf


class BowNoise(
    parameters.abc.ExplicitPlayingIndicator, abjad_attachments.BangFirstAttachment
):
    def process_leaf(self, leaf: abjad.Leaf) -> abjad.Leaf:
        leaf.written_pitch = "b'"
        leaf.written_duration = 1
        abjad.attach(
            abjad.LilyPondLiteral(
                "\\override Staff.StaffSymbol.line-count = #1", format_slot="before"
            ),
            leaf,
        )
        abjad.attach(
            abjad.LilyPondLiteral("\\once \\hide Staff.Clef", format_slot="before"),
            leaf,
        )

        abjad.attach(
            abjad.LilyPondLiteral(r"\once \omit Accidental", format_slot="before"),
            leaf,
        )

        note_head_override = r"""
\once \override NoteHead.stencil = #ly:text-interface::print
\once \override NoteHead.text = \markup {
  \hspace #-0.4
  \combine
  \musicglyph "noteheads.s2"
  \path #0.15 #'((moveto 3 1.5)
                 (lineto -1.5 -1.5)
                 (curveto -1.5 -1.5 -1.75 0.25 1.25 1.25)
                 (curveto 1.25 1.25 2.125 1.5 3 1.5)
                 (closepath))
}
"""
        abjad.attach(
            abjad.LilyPondLiteral(note_head_override, format_slot="before"), leaf,
        )
        return leaf


class TeethOnReed(
    parameters.abc.ExplicitPlayingIndicator, abjad_attachments.BangFirstAttachment
):
    def process_leaf(self, leaf: abjad.Leaf) -> abjad.Leaf:
        leaf = abjad.mutate.copy(leaf)
        leaf.written_pitch = "c'''"
        leaf.written_duration = 1
        abjad.attach(
            abjad.LilyPondLiteral(r"\once \omit Accidental", format_slot="before"),
            leaf,
        )
        abjad.attach(
            abjad.Markup(
                r"\tiny {quiet whistle tones (teeth on reed)}", direction="up"
            ),
            leaf,
        )
        abjad.attach(
            abjad.LilyPondLiteral(
                "\\once \\override Glissando.minimum-length = #70",
                format_slot="before",
            ),
            leaf,
        )
        abjad.attach(
            abjad.LilyPondLiteral(
                "\\once \\override Glissando.springs-and-rods ="
                " #ly:spanner::set-spacing-rods",
                format_slot="before",
            ),
            leaf,
        )
        fancy_glissando = r"""
\fancy-gliss
        #'(
            (1 3 0.2 2 1 1)
            (2 -3)
            (3 3)
            (4 1)
            (5 3.5)
            (6 0)
            (7 0 8 6 12 0))
"""
        abjad.attach(
            abjad.LilyPondLiteral(fancy_glissando, format_slot="before"), leaf,
        )

        voice = abjad.Voice([leaf, abjad.Note("c'''", abjad.Duration((1, 256)))])

        abjad.attach(
            abjad.LilyPondLiteral(r"\once \omit Accidental", format_slot="before"),
            voice[1],
        )
        abjad.attach(
            abjad.LilyPondLiteral(r"\once \omit NoteHead", format_slot="before"),
            voice[1],
        )

        abjad.attach(abjad.Glissando(), leaf)

        return voice


class HarmonicGlissando(
    parameters.abc.ExplicitPlayingIndicator, abjad_attachments.BangFirstAttachment
):
    def process_leaf(self, leaf: abjad.Leaf) -> abjad.Leaf:
        leaf = abjad.mutate.copy(leaf)
        leaf.written_pitch = "b'"
        leaf.written_duration = 1
        abjad.tweak(leaf.note_head).NoteHead.style = "#'harmonic"
        abjad.attach(
            abjad.LilyPondLiteral("\\once \\hide Staff.Clef", format_slot="before"),
            leaf,
        )
        abjad.attach(
            abjad.LilyPondLiteral("\\once \\omit Accidental", format_slot="before"),
            leaf,
        )

        fancy_glissando = r"""
\fancy-gliss
        #'(
            (1 3 0.2 2 1 1)
            (2 -3)
            (3 3)
            (4 1)
            (5 3.5)
            (6 0)
            (7 0 8 6 12 0))
"""
        abjad.attach(
            abjad.LilyPondLiteral(fancy_glissando, format_slot="before"), leaf,
        )

        voice = abjad.Voice([leaf, abjad.Note("b'64")])

        abjad.attach(
            abjad.LilyPondLiteral(r"\once \omit Accidental", format_slot="before"),
            voice[1],
        )
        abjad.attach(
            abjad.LilyPondLiteral(r"\once \omit NoteHead", format_slot="before"),
            voice[1],
        )

        abjad.attach(abjad.Glissando(), leaf)

        return voice


# muesste besser "CentDeivations" sein, sodass man auch Akkorde notieren kann
class CentDeviation(
    notation_indicators.CentDeviation, abjad_attachments.BangFirstAttachment
):
    def process_leaf(self, leaf: abjad.Leaf) -> abjad.Leaf:
        adjusted_deviation = None
        if isinstance(self.deviation, float):
            if self.deviation % 100 != 0:
                if self.deviation > 0:
                    prefix = "+"
                else:
                    prefix = "-"
                adjusted_deviation = round(abs(self.deviation))
        elif isinstance(self.deviation, str):
            adjusted_deviation = self.deviation
            dev = float(adjusted_deviation.split(" ")[0])
            if dev > 0:
                prefix = "+"
            else:
                prefix = ""
        if adjusted_deviation:
            markup = abjad.Markup(
                "\\tiny { " + f"{prefix}{adjusted_deviation} ct" + " } ", direction="up"
            )
            abjad.attach(
                markup, leaf,
            )
        return leaf


class PreciseDoubleHarmonic(
    playing_indicators.PreciseDoubleHarmonic, abjad_attachments.AbjadAttachment
):
    def process_leaf(
        self,
        original_leaf: abjad.Leaf,
        add_indicators: bool,
        stem_direction: bool,
        string_pitch: abjad.NamedPitch,
        played_pitch: abjad.NamedPitch,
    ) -> abjad.Voice:
        new_abjad_leaf = abjad.Chord("c", original_leaf.written_duration,)

        if stem_direction is True:
            direction = 1  # up
        else:
            direction = -1  # down
            abjad.attach(
                abjad.LilyPondLiteral(
                    "\\once \\override NoteColumn #'force-hshift = #1.5",
                    format_slot="before",
                ),
                new_abjad_leaf,
            )

        abjad.attach(
            abjad.LilyPondLiteral("\\-", format_slot="after",), new_abjad_leaf,
        )
        abjad.attach(
            abjad.LilyPondLiteral(
                f"\\once \\override Voice.Stem.direction = {direction}",
                format_slot="before",
            ),
            new_abjad_leaf,
        )
        abjad.attach(
            abjad.LilyPondLiteral(
                "\\once \\undo \\omit Staff.Stem", format_slot="before"
            ),
            new_abjad_leaf,
        )
        abjad.attach(
            abjad.LilyPondLiteral(
                "\\once \\override Staff.Stem.duration-log = 2", format_slot="before"
            ),
            new_abjad_leaf,
        )
        abjad.attach(
            abjad.LilyPondLiteral(
                "\\once \\override Staff.Stem.thickness = 2", format_slot="before"
            ),
            new_abjad_leaf,
        )

        new_abjad_leaf.written_pitches = abjad.PitchSegment(
            [string_pitch, abjad.NamedPitch("c''''''")]
        )
        new_abjad_leaf.note_heads[1]._written_pitch = played_pitch
        abjad_attachments.ArtificalHarmonic._change_note_head_style(new_abjad_leaf)

        new_voice = abjad.Voice([new_abjad_leaf])
        new_voice.consists_commands.append("Duration_line_engraver")

        if add_indicators:
            for indicator in abjad.get.indicators(original_leaf):
                if type(indicator) != dict:
                    try:
                        abjad.attach(indicator, new_voice)
                    except Exception:
                        abjad.attach(indicator, new_voice[0])

        return new_voice

    def process_leaves(
        self, leaves: typing.Tuple[abjad.Leaf, ...], _,
    ) -> typing.Tuple[abjad.Leaf, ...]:

        leaf = leaves[0]

        voices = []
        if self.played_pitch0 == self.played_pitch1:
            stem_directions = (True, True)
        elif self.string_pitch0 > self.string_pitch1:
            stem_directions = (False, True)
        else:
            stem_directions = (True, False)

        for stem_direction, attach_indicators, string_pitch, played_pitch in zip(
            stem_directions,
            (True, False),
            (self.string_pitch0, self.string_pitch1),
            (self.played_pitch0, self.played_pitch1),
        ):
            voice = self.process_leaf(
                leaf, attach_indicators, stem_direction, string_pitch, played_pitch
            )
            for rest_leaf in leaves[1:]:
                voice.append(abjad.mutate.copy(rest_leaf))
            voices.append(voice)
        voices = abjad.Container(voices, simultaneous=True)
        return (voices,)


# override mutwo default value
mutwo_abjad_constants.DEFAULT_ABJAD_ATTACHMENT_CLASSES = (
    mutwo_abjad_constants.DEFAULT_ABJAD_ATTACHMENT_CLASSES
    + (
        ExplicitFermata,
        Noise,
        CentDeviation,
        PreciseDoubleHarmonic,
        BendBefore,
        EmptyGraceContainer,
        Fingering,
        CombinedFingerings,
        BowNoise,
        HarmonicGlissando,
        TeethOnReed,
    )
)
