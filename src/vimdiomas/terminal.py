"""Terminal capability detection and the kitty graphics protocol encoder.

Detection is env-var based (`TERM_PROGRAM`/`TERM`), not a capability query —
no I/O, no risk of hanging on a terminal that doesn't answer (M4's spec
decision)."""

import base64
import os

# Known TERM_PROGRAM values for terminals that speak the kitty graphics
# protocol. `kitty` itself sets TERM=xterm-kitty rather than TERM_PROGRAM in
# some configs, checked separately below.
_KITTY_TERM_PROGRAMS = {"ghostty", "wezterm", "kitty"}

_CHUNK_SIZE = 4096


def supports_kitty_graphics() -> bool:
    """Whether the current terminal is known to speak the kitty graphics
    protocol, judged from environment variables alone."""
    term_program = os.environ.get("TERM_PROGRAM", "").lower()
    if term_program in _KITTY_TERM_PROGRAMS:
        return True
    return os.environ.get("TERM", "") == "xterm-kitty"


def clear_kitty_images() -> str:
    """The kitty graphics protocol's delete-all-placements escape sequence.

    Kitty images sit in their own layer above the text grid — redrawing the
    cells underneath (Textual painting a message or the menu screen over
    where a preview used to be) does not by itself make the terminal drop
    the image, so this has to be sent explicitly whenever a previously shown
    image should disappear (switching to a message, leaving the screen, or
    just before drawing a new image, in case it's smaller than the old one).
    """
    return "\x1b_Ga=d;\x1b\\"


def render_kitty_image(png_bytes: bytes) -> str:
    """Encode `png_bytes` as a kitty graphics protocol escape sequence,
    ready to write directly to the terminal.

    `a=T` transmits and displays immediately; `f=100` says the payload is
    already PNG-encoded, so no raw-pixel format/size keys are needed. Large
    payloads are split into base64 chunks of at most 4096 bytes each, with
    `m=1` on every chunk but the last (the protocol's own chunking rule).
    """
    payload = base64.b64encode(png_bytes).decode("ascii")
    chunks = [payload[i : i + _CHUNK_SIZE] for i in range(0, len(payload), _CHUNK_SIZE)]
    if not chunks:
        chunks = [""]

    parts = []
    last_index = len(chunks) - 1
    for index, chunk in enumerate(chunks):
        more = "1" if index < last_index else "0"
        control = f"a=T,f=100,m={more}" if index == 0 else f"m={more}"
        parts.append(f"\x1b_G{control};{chunk}\x1b\\")
    return "".join(parts)


def cell_pixel_size() -> tuple[int, int]:
    """Best-effort (width, height) in pixels of one terminal cell, used to
    turn a widget's cell-based region into a target raster resolution.

    Opens `/dev/tty` directly rather than using `sys.stdout` — Textual's
    driver replaces `sys.stdout` with something whose `fileno()` returns -1
    while the app is running, which `fcntl.ioctl` rejects with a `ValueError`
    before it ever gets the chance to fail as an `OSError`. Falls back to a
    typical monospace cell size when the terminal doesn't report pixel
    dimensions either (`TIOCGWINSZ`'s xpixel/ypixel come back 0, as they do
    over some multiplexers/SSH hops)."""
    try:
        import fcntl
        import struct
        import termios

        with open("/dev/tty") as tty:
            packed = fcntl.ioctl(tty.fileno(), termios.TIOCGWINSZ, b"\0" * 8)
        rows, cols, xpixels, ypixels = struct.unpack("HHHH", packed)
        if cols and rows and xpixels and ypixels:
            return (xpixels // cols, ypixels // rows)
    except (OSError, ValueError):
        pass
    return (10, 20)
