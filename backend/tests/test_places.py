from app.services.places import format_reverse_geocode_label


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
