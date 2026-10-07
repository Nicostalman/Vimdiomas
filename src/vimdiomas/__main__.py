"""The entry point: the support gate (Sprint 8 M1), then the real `main` in
`cli.py`.

The gate runs before `cli` is imported because `cli`'s imports are what reach
`vimdiomas.platform`, and before anything writes (`migrate_legacy_paths`).
The console script stays `vimdiomas.__main__:main`."""

from vimdiomas import supported_os


def main() -> None:
    supported_os.refuse_unless_supported()
    from vimdiomas import cli

    cli.main()


if __name__ == "__main__":
    main()
