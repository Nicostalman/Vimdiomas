# M1 · Data integrity — plan

Task groups, ordered so later groups depend only on earlier ones. Groups 1–3 are
the storage layer, 4–5 the config, 6–7 the Entry form, 8 Inspect Tree, 9 docs.

Every group starts by **re-reproducing its finding as a failing test**, per
`notes-sprint-6.md`'s first Assumption: the report was written against commit
`aa11572` and each finding is confirmed still live before it is fixed.

## 1. #2 — the empty-field split

- `parser.parse`: in the entry branch, split `raw_line.rstrip("\n\r")` on `\t`
  instead of `stripped`, then `.strip(" ")` each field. Guard unchanged
  (`raw_line.count("\t") >= 2`).
- A split yielding fewer than three fields appends a
  `Warning(line_number, "malformed entry row", raw_line)` and skips the line
  (`last_entry = None`), rather than unpacking.
- Tests (`test_parser.py`):
  - `你\tni3\t` parses to `Entry(hanzi="你", pinyin="ni3", gloss="")` with no
    warning and no exception — the report's own P1 reproduction.
  - `\tni3\tyou` (empty leading field) parses with an empty `hanzi`.
  - `你\t\t` (both trailing fields empty) parses.
  - A whitespace-only translation (`你\tni3\t   `) parses to an empty gloss.
  - A **space-indented** entry row parses exactly as it does today.
  - A row with **padded inner fields** now parses with each field stripped of
    spaces on its own (a behaviour change; see requirements.md).
  - A **tab-indented** triad row reads as an empty first field (a behaviour
    change, from an exception; see requirements.md).
  - Extra fields beyond three still land in `extra_fields`, unchanged.
  - Round trip: each of the above through `write` → `parse` is identical.
- Tests (`test_tui_entry_screen.py`): creating an entry with an empty
  translation through the form, then re-parsing the file, gives the entry back —
  the vocabulary form and the grammar form both.
- Tests (`test_store.py`): `walk()` over a tree containing a file with such a
  row returns the tree instead of raising (this is the "locks the user out of
  the whole tree" half of the finding).

## 2. #3 — tag round-tripping

- `writer._render_tag(tag)`:
  - no whitespace and no `"`, `'` or `\` → `#{tag}` (unchanged);
  - no `"` and no `\` → `#"{tag}"` (unchanged output for a whitespace tag,
    and the same form now covers a tag with an apostrophe — see
    requirements.md's *Refinements*);
  - otherwise → `shlex.quote("#" + tag)`.
- `parser._parse_tags_line`: wrap `shlex.split` in `try/except ValueError`,
  returning `None` on failure so the caller can emit a warning.
- `parser.parse`'s tags branch: on a failed split, append
  `Warning(line_number, "unparseable tag syntax", raw_line)` and add no tags.
- Tests (`test_writer.py` / `test_parser.py`):
  - Property: for every tag in a corpus — `don't`, `"quoted"`, `a b`,
    `back\slash`, `#"don't"`'s parsed form, `a'b"c`, `a\"b`, a tag with a tab
    (after M1's sanitiser, still worth asserting) — `_parse_tags_line(_render_tag(t)) == [t]`.
  - The report's exact reproduction: a Tags section containing `#"don't"` parses
    to `don't`, `write()` of that deck re-parses to the same deck, and the
    written text does not raise `ValueError: No closing quotation`.
  - Tags already in the dev's tree (plain, and whitespace-quoted) are written
    **byte-identically** to today — a fixture comparison, so the fix cannot
    reformat existing files.
  - A Tags line with an unclosed quote produces a warning and no tags, and does
    not raise.

## 3. #15 — the writer's tab guard

- `writer._render_entries`: raise `ValueError` naming the entry and the field if
  any of `hanzi`, `pinyin`, `gloss` or `extra_fields` contains `\t`, `\n` or
  `\r`. (`note` is written on its own line and cannot shift columns, but a
  newline in it would break the file, so it is checked for `\n`/`\r` too.)
- Tests (`test_writer.py`): each field in turn containing a tab raises; a
  well-formed deck is unaffected.

## 4. #6 — a correct TOML encoder

- `config._toml_string(value: str) -> str`: a value with no `'`, no `\` and no
  control character is a TOML **literal** string, `'{value}'` — byte-for-byte
  what `!r` produced for it. Anything else is a TOML **basic** string: wrap in
  `"`, escaping `\` → `\\`, `"` → `\"`, `\b`/`\t`/`\n`/`\f`/`\r` as their
  named escapes, and any other C0 control or DEL as `\uXXXX`. See
  requirements.md's *Refinements* for why the literal branch exists.
- `config._toml_lines`: use `_toml_string` for `user_name`, `root` and every
  language field, in place of `!r`.
- `config.save_config`: after building the text and before writing the temp
  file, `tomllib.loads` it and assert the parsed document round-trips to the
  same values as `config` (name, root string, and each language's three
  fields). A mismatch raises `ValueError`; nothing is written.
- Tests (`test_config.py`), all against a temp `CONFIG_PATH`:
  - The report's reproduction: `user_name = "O'Brien \"Nico\""` saves and
    `load_config()` returns it.
  - A name containing both quote characters **and** a backslash (the done-when
    line's exact case) round-trips.
  - A root path containing a quote and a backslash round-trips.
  - A language name / input-method id containing a quote round-trips.
  - Control characters (`\n`, `\t`, `\x00`) in a name round-trip.
  - An ordinary config's encoded text is **byte-identical** to today's `!r`
    output, asserted against `!r` itself, so no existing config is reformatted.
  - A deliberately broken encoder (monkeypatched `_toml_string`) makes
    `save_config` raise and leaves the existing file untouched.

## 5. #7 — absolute tree roots

- `wizard.RootScreen._next`: store `Path(raw).expanduser().resolve()`.
- `config.load_config`: if the stored `root` is not absolute, return
  `(Path.home() / root).resolve()` instead.
- Tests (`test_tui_wizard.py`): a relative root typed into the wizard is stored
  absolute — asserted against the saved config, from a `chdir`'d temp directory.
- Tests (`test_config.py`): a config file written by hand with a relative `root`
  loads to the same absolute path from two different working directories.
- Tests: the report's reproduction — finish setup from directory A, `chdir` to
  B, load and discover the tree — finds the tree.

## 6. #15 — sanitising form fields

- `panels.sanitise_field_text(value)`: every `\t` and every other C0 control
  character and DEL → a single space.
- `panels.TextField.validate_value`: the reactive's own validation hook, which
  Textual runs *before* posting `Changed` — so no listener ever sees an
  unsanitised value, a programmatic assignment is covered as well as a
  keystroke or paste, and cursor handling stays `Input`'s (the replacement is
  1:1, so the position never shifts). Replaces the `Input.Changed` handler the
  spec first called for; see requirements.md's *Refinements*.
- `entry.EntryScreen._on_hanzi_changed`: read
  `self.query_one("#hanzi", Input).value` rather than `event.value`.
- Tests (`test_tui_panels.py`): pasting/typing a tab into a `TextField` leaves a
  space; a NUL and a `\x1b` likewise; ordinary text is untouched; leading and
  trailing spaces are preserved.
- Tests (`test_tui_entry_screen.py`), the report's reproduction: paste
  `苹果<TAB>apple` into Hanzi, type `apple` into Translation, Create — the saved
  row has exactly three fields, hanzi is `苹果 apple`, and the guessed pinyin
  contains no tab. Repeat for Translation, Note, and the grammar form's
  subtitle-name and category-name fields.

## 7. #8 and #18 — category names

- `entry.RESERVED_CATEGORY_NAMES = {"Tags"}`, with a comment naming
  `parser.py`'s `## Tags` check as the reason it is exactly this string.
- `entry.EntryScreen._create_category`, after the existing empty-name guard:
  - name in `RESERVED_CATEGORY_NAMES` →
    `self.notify(f"{name} is reserved and can't be a category name.", severity="error")`,
    return; nothing read, nothing written, focus unchanged.
  - a category of that exact name already in the deck → run the existing
    post-create block (add nothing; move the cursor to the **existing** leaf,
    set `_active_target`, `_clear_form`, `_apply_target_state`,
    `_focus_first_field`) and notify `f"{name} already exists — selected."`;
    no `save`.
  - otherwise → today's path.
- Locating the existing leaf: search the current file node's children for the
  leaf whose `data.category_name` matches, rather than adding one.
- Tests (`test_tui_entry_screen.py`):
  - `Tags` (and `  Tags  `, which strips to it) is refused: an error
    notification, the file on disk unchanged, no new tree leaf.
  - `tags` (lowercase) is **accepted** — it is not the reserved heading.
  - Creating `Food` in a deck that already has `Food`: no second `## Food` in
    the file, the cursor lands on the existing leaf, `_active_target` is that
    category, and an entry created immediately afterwards lands under the
    existing heading.
  - Both, through the grammar form as well as the vocabulary one.
  - The report's #8 follow-on — adding an entry to a just-created category — no
    longer raises `StopIteration` for either case.

## 8. #1 — pending deletes across a rename

- `inspect.PendingDelete` dataclass: `data: NodeData`, `dev: int`, `ino: int`.
  `_pending_deletes` becomes `list[PendingDelete]`.
- `action_delete`'s `_handle`: `os.stat` the path when the deletion is
  confirmed and store the identity alongside it. A path that cannot be stat'd
  at that moment is not marked (notify, return).
- `action_rename`'s directory branch, **after** a successful `rename`: for every
  pending delete whose path is the renamed directory or lies beneath it, rewrite
  the path to the new location (`new_path / old.relative_to(old_path)`). The
  file branch does the same for an exactly-matching path.
- `on_unmount`, per pending delete:
  - path does not exist → skip silently;
  - `os.stat` identity differs from the recorded one → skip and
    `app.notify(f"{name} changed since it was deleted — left alone.", severity="warning")`;
  - otherwise → delete as today (and the sibling `.pdf` for a file).
- `_prune`/`_rebuild_tree`/`action_undo` read `.data.path` off the new type;
  behaviour otherwise unchanged.
- Tests (`test_tui_inspect_tree.py`):
  - The report's reproduction in full: delete `Old/DeleteMe.md`, rename `Old` →
    `New`, rebuild — the file stays hidden (it does not reappear); recreate
    `Old/DeleteMe.md` with different content; leave the screen — `New/DeleteMe.md`
    is gone and `Old/DeleteMe.md` survives with its content intact.
  - Rename an ancestor two levels up; the pending path is still remapped.
  - Delete a file, replace it at the same path with a different file, leave —
    the replacement survives and a warning notification is posted.
  - Delete a directory, rename its parent, leave — the directory is removed at
    its new location.
  - Delete a file, then `u` — unchanged behaviour, nothing is removed on leaving.
  - Delete a file, delete it externally, leave — no error, no notification.

## 9. Docs

- `specs/current/stack.md`:
  - the *Installation and config* section gains the TOML encoder (local, not a
    dependency, with the same rationale the section already gives for reading
    the macOS plist with `plistlib`) and the validate-before-replace step;
  - and the rule that the stored `root` is always absolute, with the
    home-relative recovery for older configs.
- `specs/current/stack.md`'s *Storage* section also gains the rules the format
  itself implies, which this milestone is what makes true: no field may contain
  a tab or a newline (stripped at the field, refused at the writer), a row is
  split with only its terminator removed, tags are written the way `shlex`
  reads them, and an unreadable line is a warning rather than an exception
  because both tree screens parse every file to build themselves.
- `specs/current/design.md`: three new subsections under *Navigation
  conventions*, stating as conventions rather than screen-local details —
  - **Names the app refuses**: the category-name rules (`Tags` refused with an
    error notification, a duplicate name selecting the existing category), and
    the standing shape for a refused name. M2 extends this one with Inspect
    Tree's path-prompt rules; it is written here so it has one home rather than
    two.
  - **Fields sanitise what is pasted into them**: #15's rule, which applies to
    every field on every screen.
  - **Inspect Tree's deferred deletes**: that a rename carries a deletion
    marked beneath it, that the mark is on the file rather than its path, and
    what the user is told in each case.
- Update this milestone's three spec files as anything changes during
  implementation.
