from app.services.places import format_reverse_geocode_label, format_reverse_geocode_place_name


def test_format_reverse_geocode_label_prefers_short_human_readable_address() -> None:
    payload = {
        "display_name": "129, Sundance Court, Sangaree, Berkeley County, South Carolina, 29486, United States",
        "address": {
            "house_number": "129",
            "road": "Sundance Court",
            "suburb": "Sangaree",
            "state": "South Carolina",
            "postcode": "29486",
            "country": "United States",
        },
    }

    assert format_reverse_geocode_label(payload) == "129 Sundance Court, Sangaree, South Carolina 29486"


def test_format_reverse_geocode_label_can_fall_back_to_block_level() -> None:
    payload = {
        "display_name": "129, Sundance Court, Sangaree, Berkeley County, South Carolina, 29486, United States",
        "address": {
            "house_number": "129",
            "road": "Sundance Court",
            "suburb": "Sangaree",
            "state": "South Carolina",
            "postcode": "29486",
        },
    }

    assert format_reverse_geocode_label(payload, granularity="block") == "100 block of Sundance Court, Sangaree"


def test_format_reverse_geocode_label_can_fall_back_to_street_level() -> None:
    payload = {
        "display_name": "129, Sundance Court, Sangaree, Berkeley County, South Carolina, 29486, United States",
        "address": {
            "house_number": "129",
            "road": "Sundance Court",
            "suburb": "Sangaree",
            "state": "South Carolina",
            "postcode": "29486",
        },
    }

    assert format_reverse_geocode_label(payload, granularity="street") == "Sundance Court, Sangaree"


def test_format_reverse_geocode_place_name_prefers_named_destination() -> None:
    payload = {
        "name": "Target",
        "display_name": "Target, 129, Sundance Court, Sangaree, Berkeley County, South Carolina, 29486, United States",
        "address": {
            "shop": "Target",
            "house_number": "129",
            "road": "Sundance Court",
            "suburb": "Sangaree",
            "state": "South Carolina",
            "postcode": "29486",
        },
    }

    assert format_reverse_geocode_place_name(payload) == "Target"
