import typing

from mutwo import events

Serenade = events.basic.SimultaneousEvent[events.basic.TaggedSequentialEvent]


def _post_process_serenade0(serenade: Serenade):
    for pizz_events in (31, 55):
        serenade[0][
            pizz_events
        ].playing_indicators.string_contact_point.contact_point = (
            "pizzicato"
        )

    for arco_events in (30, 32, 53):
        serenade[0][
            arco_events
        ].playing_indicators.string_contact_point.contact_point = (
            "ordinario"
        )

    for bartok_pizz_event in (58,):
        serenade[0][
            bartok_pizz_event
        ].playing_indicators.bartok_pizzicato.is_active = True

    for ottava_event in range(23, 33):
        serenade[0][ottava_event].notation_indicators.ottava.n_octaves = 1

    for slap_event in (-2,):
        serenade[1][slap_event].playing_indicators.articulation.name = "^"
        serenade[1][slap_event].notation_indicators.markup.content = r"\teeny {(slap)}"
        serenade[1][slap_event].notation_indicators.markup.direction = r"down"

    for breath_mark_event in (4,):
        serenade[1][breath_mark_event].playing_indicators.breath_mark.is_active = True


def _post_process_serenade1(serenade: Serenade):
    for breath_mark_event in (5, 15):
        serenade[1][breath_mark_event].playing_indicators.breath_mark.is_active = True


def _post_process_serenade2(serenade: Serenade):
    for natural_harmonic_event in (5,):
        serenade[0][
            natural_harmonic_event
        ].playing_indicators.natural_harmonic.is_active = True
    for pizz_events in (14, 16):
        serenade[0][
            pizz_events
        ].playing_indicators.string_contact_point.contact_point = (
            "pizzicato"
        )
    
    # bend before makes error with quantization
    # for bend_before_vl in (18,):
    #     serenade[0][bend_before_vl].playing_indicators.bend_before.bend_interval = -4
    #     serenade[0][bend_before_vl].playing_indicators.bend_before.bend_length = 5

    # for bend_before_sax in (18,):
    #     serenade[1][21].playing_indicators.bend_before.bend_interval = -3
    #     serenade[1][21].playing_indicators.bend_before.bend_length = 4

    for arco_events in (13, 15, 18):
        serenade[0][
            arco_events
        ].playing_indicators.string_contact_point.contact_point = (
            "ordinario"
        )


def main(serenades: typing.Dict[str, Serenade], definitions):
    _post_process_serenade0(serenades[definitions.ID_SERENADE0])
    _post_process_serenade1(serenades[definitions.ID_SERENADE1])
    _post_process_serenade2(serenades[definitions.ID_SERENADE2])
