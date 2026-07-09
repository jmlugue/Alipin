from alipin.router import route_command


def test_routes_note_command():
    intent = route_command("take a note buy oat milk")

    assert intent.name == "note"
    assert intent.payload == "buy oat milk"


def test_routes_app_command():
    intent = route_command("open browser")

    assert intent.name == "app"
    assert intent.payload == "browser"


def test_routes_question():
    intent = route_command("what is the weather?")

    assert intent.name == "qa"
