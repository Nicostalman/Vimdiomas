import base64

from vimdiomas import terminal


def test_supports_kitty_graphics_for_known_term_programs(monkeypatch):
    for value in ["ghostty", "wezterm", "kitty", "Ghostty", "WezTerm"]:
        monkeypatch.setenv("TERM_PROGRAM", value)
        monkeypatch.delenv("TERM", raising=False)
        assert terminal.supports_kitty_graphics() is True


def test_supports_kitty_graphics_for_xterm_kitty_term(monkeypatch):
    monkeypatch.delenv("TERM_PROGRAM", raising=False)
    monkeypatch.setenv("TERM", "xterm-kitty")
    assert terminal.supports_kitty_graphics() is True


def test_supports_kitty_graphics_false_for_unknown_or_unset(monkeypatch):
    monkeypatch.delenv("TERM_PROGRAM", raising=False)
    monkeypatch.setenv("TERM", "xterm-256color")
    assert terminal.supports_kitty_graphics() is False

    monkeypatch.delenv("TERM", raising=False)
    assert terminal.supports_kitty_graphics() is False


def test_supports_kitty_graphics_false_for_iterm(monkeypatch):
    monkeypatch.setenv("TERM_PROGRAM", "iTerm.app")
    monkeypatch.delenv("TERM", raising=False)
    assert terminal.supports_kitty_graphics() is False


def _decoded_payload(sequence: str) -> bytes:
    """Pull the base64 payload out of every APC chunk in `sequence` and
    concatenate it back into the original bytes."""
    payload = ""
    remaining = sequence
    while remaining:
        start = remaining.index("\x1b_G") + len("\x1b_G")
        end = remaining.index("\x1b\\", start)
        chunk = remaining[start:end]
        payload += chunk.split(";", 1)[1]
        remaining = remaining[end + len("\x1b\\") :]
    return base64.b64decode(payload)


def test_render_kitty_image_round_trips_small_png():
    png_bytes = b"\x89PNG\r\n\x1a\nfake-small-png-body"
    sequence = terminal.render_kitty_image(png_bytes)
    assert sequence.startswith("\x1b_G")
    assert _decoded_payload(sequence) == png_bytes


def test_render_kitty_image_chunks_large_payload():
    png_bytes = b"x" * 10_000
    sequence = terminal.render_kitty_image(png_bytes)
    # More than one 4096-byte base64 chunk needed for this payload size.
    assert sequence.count("\x1b_G") > 1
    assert _decoded_payload(sequence) == png_bytes
    assert "m=0;" in sequence  # the final chunk marks no more data


def test_cell_pixel_size_falls_back_when_ioctl_fails(monkeypatch):
    import fcntl

    def _raise(*args, **kwargs):
        raise OSError("not a tty")

    monkeypatch.setattr(fcntl, "ioctl", _raise)
    assert terminal.cell_pixel_size() == (10, 20)
