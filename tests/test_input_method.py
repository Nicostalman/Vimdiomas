from vimdiomas import input_method
from vimdiomas.input_method import switch_to


def test_switch_to_passes_the_source_id_through(monkeypatch):
    calls = []
    monkeypatch.setattr(input_method, "switch_input_source", calls.append)

    switch_to("com.apple.inputmethod.SCIM.ITABC")

    assert calls == ["com.apple.inputmethod.SCIM.ITABC"]


def test_switch_to_does_nothing_without_a_configured_source(monkeypatch):
    """An unconfigured language must not reach the platform layer at all —
    that only happens with no enabled input sources, where there is nothing
    to switch to."""
    calls = []
    monkeypatch.setattr(input_method, "switch_input_source", calls.append)

    switch_to("")

    assert calls == []
