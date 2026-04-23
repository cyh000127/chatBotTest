from PROJECT.channels.telegram.handlers.messages import parse_callback_data


def test_parse_yield_edit_callback_data():
    action, payload = parse_callback_data("yield:edit:amount")

    assert action == "yield_edit_select"
    assert payload == {"target": "amount"}
