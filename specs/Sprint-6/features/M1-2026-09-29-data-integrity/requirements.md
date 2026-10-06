# M1 · Data integrity — requirements

## Anchor (from the roadmap)

The first tier of [`../../guidelines/bug-report.md`](../../guidelines/bug-report.md)'s
recommended order: every finding where the app writes something it cannot read
back, or acts on the wrong file. These are the ones that cost the user data or
lock them out of their own tree.

**Findings in scope:** #1, #2, #3, #6, **#7**, #8, #15, #18.

**Deliverable.**

- **A pending delete stops surviving a rename of its parent** (#1, P1). Today
  deleting `Old/DeleteMe.md` and then renaming `Old/` to `New/` un-deletes the
  file in the tree and leaves the pending path pointing at something that may
  by then be a different file — on leaving Inspect Tree, the wrong file is the
  one that goes. Either the pending paths are remapped with the rename or the
  rename is refused while descendant deletions are pending; either way a
  destructive commit verifies the target is still what was marked.
- **An entry with an empty field round-trips** (#2, P1). `你\tni3\t` is
  writable through the form today and unparseable afterwards — and because both
  tree screens parse every file to build themselves, one such row locks the
  user out of the whole tree. The split stops discarding empty boundary fields,
  and a malformed row becomes a diagnostic rather than an exception escaping
  discovery.
- **Tags survive a write** (#3). The parser reads tags with `shlex`; the writer
  quotes only whitespace. `#"don't"` parses and then rewrites to `#don't`,
  which no longer parses — so adding an unrelated entry corrupts the file's tag
  block. Writing becomes `shlex`-compatible, and unparseable tag syntax is a
  warning rather than a crash.
- **The config survives an apostrophe** (#6). `config.py` serializes with
  Python's `!r`, which is not TOML. A user named `O'Brien` finishes the wizard
  and cannot launch the app again. A real TOML encoder replaces it, and the
  document is validated before it replaces the existing file.
- **Reserved and duplicate category names are refused** (#8, #18). `Tags` as a
  category name produces a heading the parser reads as metadata, and a second
  `Food` produces a heading nothing can ever reach. Both are rejected at the
  form with a visible message and no file written — or, for the duplicate, the
  existing category is selected, as subtitle creation already does.
- **A tab pasted into a field cannot shift the columns** (#15). Control
  characters are stripped or rejected at the form, and the writer refuses to
  emit a field containing a tab.

**Done when.** Each of the seven findings has a regression test matching the
report's *Regression coverage* line; the two P1 reproductions no longer
reproduce; a config containing both quote characters and a backslash saves and
reloads; the dev confirms by hand in their own tree; and the full test suite
passes.

Backlog source:
[`../../guidelines/backlog.md`](../../guidelines/backlog.md)'s *Bug fixes*
section, which reads in full "see the file bug-report" — so the report itself is
the requirement text, cited below by finding number throughout.

## Scope change agreed at spec time: finding #7 joins M1

The roadmap's three bug milestones between them list **18 of the report's 19
findings**. #7 — *Relative notebook roots depend on the launch directory* — is
in none of them. The report's own recommended order pairs it with #9 at step 5;
#9 landed in M2 and #7 fell out of the fold from six steps into three
milestones.

Raised with the dev at spec time and **added to M1**: it is a
config-serialization bug in the same function as #6, it costs the user access to
their own tree exactly as the rest of this tier does, and M1 is already
rewriting `config.py`. The roadmap's *Findings in scope* line for M1 is
therefore eight findings, not seven, and its done-when bar is eight regression
tests, not seven.

**Added deliverable.**

- **A tree root is stored absolute** (#7). The wizard validates a resolved path
  but stores `Path(raw).expanduser()`, so a relative answer is re-interpreted
  against every future process's working directory: the same command finds a
  different tree, or none, depending on where it was launched. The wizard
  resolves before storing, and a config that already holds a relative root gets
  an explicit, stable recovery.

## Decisions from the spec conversation (2026-09-29)

| Decision | Rationale |
| --- | --- |
| **Finding #7 joins M1** | Dev's choice from three (M1 / M2 / postpone). It is the same class of bug as #6 in the same file, and M1 is the tier for "the app wrote something it cannot use". |
| **An entry with an empty translation stays writable** | Dev's choice from three. Only the parser is fixed: hanzi remains the single required field, and a row with an empty translation saves, reloads and compiles with an empty third column. `mission.md`'s "must read back anything a reasonable hand-edit produces" means the parser has to accept such a row whatever the form does, so forbidding it at the form would buy nothing and cost a working input. |
| **A duplicate category name selects the existing category** rather than being refused | Dev's choice from three. It is exactly what subtitle creation already does (`entry.py:416`), so the two creation paths stop differing; no new message and no new rule. |
| **A reserved category name (`Tags`) is refused with a visible message**, no file written | Dev's choice, bundled with the above — each case gets its own best answer. Unlike a duplicate there is nothing to select: the heading the writer would emit is unreachable by construction. |

## Decisions taken while speccing (agent)

Everything below was delegated by the dev ("the feature spec for the bugs is up
to you, unless it's an undefined design decision").

### #1 — pending deletes and renames

| Decision | Rationale |
| --- | --- |
| **Remap, don't refuse.** Renaming a directory rewrites every pending delete path beneath it to the new location | The roadmap allows either. Refusing would make a rename fail for a reason the user cannot see on screen — the deleted file is hidden from the tree, so "you can't rename this, something under it is pending" names something invisible. Remapping is what the user already believes happened. |
| **A pending delete carries the file's identity, not just its path**: `(st_dev, st_ino)` captured with `os.stat` at the moment `d` is confirmed | This is the report's "verify the pending item is still the intended file before committing destructive operations", made checkable. A path can be re-created between marking and committing — the report's own reproduction does exactly that. |
| **At commit time (`on_unmount`), a target whose identity no longer matches is skipped**, and the user is notified that it was left alone | Not deleting is always the recoverable direction. The notification is `app.notify`, which survives the screen leaving because it belongs to the app. |
| **A pending delete whose path no longer exists at commit time is dropped silently** | It is already gone; there is nothing to report and nothing to do. |
| **`u` (undo) is unchanged** | It pops the pending list; remapping keeps that list correct rather than changing how it is consumed. |

### #2 — the empty-field split

| Decision | Rationale |
| --- | --- |
| **The entry branch splits the line with only its line terminator removed** (`raw_line.rstrip("\n\r")`), not `stripped` | `strip()` removes tabs as whitespace, which is precisely how the trailing empty field disappears before `split("\t")` ever runs. The `>= 2 tabs` guard already ran against `raw_line`, so the two now agree on the same string. |
| **Each field is then stripped of spaces individually** (`field.strip(" ")`), not of tabs | Preserves today's behaviour for an indented or space-padded row while leaving field boundaries alone. |
| **A row that still yields fewer than three fields is a `Warning` and is skipped**, never an exception | Defensive: with the guard above it should be unreachable, but the whole point of this finding is that one bad row must not be able to escape tree discovery. M9 is what will show the warning; M1 only has to produce it. |
| **No new validation is added at the form** | Follows from the dev's decision above. |

### #3 — tag round-tripping

| Decision | Rationale |
| --- | --- |
| **`_render_tag` picks the narrowest form that round-trips**: a tag with no whitespace and no `"`, `'` or `\` writes as `#tag` (today's output); a tag with whitespace but no `"` or `\` writes as `#"tag"` (today's output); anything else writes as `shlex.quote("#" + tag)` | Keeps every tag already in the dev's tree byte-identical on rewrite — a correctness fix that reformatted the whole tag block of every file would be a worse outcome than the bug. Only the cases that are broken today change. |
| **The property, not the format, is what is tested**: `_parse_tags_line(_render_tag(t)) == [t]` over a corpus covering apostrophes, double quotes, backslashes, whitespace and combinations | The report's regression line is a round trip; asserting the exact string for each case would freeze an implementation detail. |
| **`shlex.split` raising becomes a `Warning` on that line**, and the line contributes no tags | The roadmap's "unparseable tag syntax is a warning rather than a crash". Same treatment as any other unrecognized line, and it is what stops an already-corrupted file from locking the tree. |
| **A tag whose own text starts with `#` is out of scope** | `_parse_tags_line` strips *all* leading `#`, so such a tag cannot round-trip today either. Not in the report, not reproduced, and fixing it would change the storage format. Recorded in *Out of scope*. |

### #6 — TOML serialization

| Decision | Rationale |
| --- | --- |
| **A small correct encoder in `config.py`, not a dependency** | The project's standing pattern, documented in `stack.md`: the numbered↔tone-mark conversion, the fuzzy scorer and the macOS plist reading are all local because each is "a small, exactly-specified transformation not worth a dependency". What the config writes is two scalar types (string, array of tables); the TOML basic-string escape rule is about ten lines. Adding `tomli-w` for it would be the first runtime dependency added for less. |
| **Strings are written as TOML *basic* strings** with `\` → `\\`, `"` → `\"`, `\b\t\n\f\r` as their escapes, and any other C0 control or DEL as `\uXXXX` | This is the TOML 1.0 basic-string grammar in full for the characters that can appear here. Literal (single-quoted) strings were rejected: they cannot express a `'`, which is the report's own reproduction. |
| **The document is validated before it replaces the config**: the encoded text is parsed back with `tomllib` and the parsed values compared against the `Config` that produced them; a mismatch raises and nothing is written | The report asks for validation, and this is the form that actually catches an encoder bug rather than just a syntax error. It also means a future field added to `Config` without an encoder case fails loudly at save time instead of silently at next launch. |
| **The atomic temp-file + `os.replace` save is unchanged** | Already correct, and already the project's standing convention. |

### #7 — absolute tree roots

| Decision | Rationale |
| --- | --- |
| **The wizard stores `Path(raw).expanduser().resolve()`** | `validate_tree_root` already resolves the path to validate it; only storage kept the unresolved form. Resolving at wizard time preserves what the user meant, since they typed the path relative to the directory they were standing in. |
| **Recovery policy for an existing relative root: `load_config` resolves it against `Path.home()`**, not against the current working directory, and the resolved value is what the rest of the app sees | A relative root in a stored config is unusable by definition — the bug is that its meaning changes per launch. Anchoring it to something stable makes the app behave the same way every time, which is the property that was missing. Home is the only fixed directory the app can name. |
| **A config with a relative root is not rewritten on load** | Loading is a read; the app does not edit the user's config behind their back. The next `save_config` (Settings, or any future write) stores the resolved form. |
| **`validate_tree_root` is unchanged** | It already resolves. |

### #8 / #18 — category names

| Decision | Rationale |
| --- | --- |
| **`Tags` is reserved, matched exactly (case-sensitive) after the existing `.strip()`** | `parser.py` reserves the literal heading `## Tags` and nothing else: a category named `tags` writes as `## tags`, which parses as an ordinary category and works. Refusing it would reject a name that is not broken. Rejecting precisely what breaks is the rule. |
| **The refusal message is an `app.notify` at `error` severity**, the category-name field keeps focus, and nothing is written | Inspect Tree already reports a refused name this way (`"{name} already exists."`), so this is the app's existing shape for "that name won't do" rather than a new one. Entry has no inline error widget, and adding one for a single case would be a new convention for this screen. |
| **A duplicate name moves the tree cursor to the existing category and makes it the active target**, notifying `"<name> already exists — selected."`; no file is written | The dev's decision, implemented as subtitle creation already implements it. The cursor move and target update reuse `_create_category`'s existing post-create path verbatim, minus the write. |
| **Both rules apply to grammar files identically** | `_create_category` is one method serving both; the parser reserves `## Tags` in both. |
| **Comparison for the duplicate check is exact**, not case-insensitive | Two categories differing only in case are two reachable headings; the parser and every lookup treat them as distinct, so neither is unreachable and there is no bug to fix. |

### #15 — control characters in fields

| Decision | Rationale |
| --- | --- |
| **`TextField` sanitises its own value as it changes**: every tab and every other C0 control character (and DEL) becomes a single space; the cleaned value is written back to the field | Doing it at the widget means the user *sees* the result before pressing Create — nothing is silently altered at save time, which is the spirit of `mission.md`'s "never silently discard". It also covers every field on every screen built on `TextField` at once, including ones added later. |
| **A tab becomes a space rather than being deleted** | The report's own reproduction is a spreadsheet row, `苹果<TAB>apple`. Deleting the tab glues two cells into `苹果apple`; a space keeps the boundary visible so the user can fix it. |
| **Leading/trailing whitespace is left alone by the sanitiser** | Trimming as the user types would fight them mid-word. The writer and parser already handle edge spaces. |
| **Entry's hanzi→pinyin auto-fill reads the field's current value, not `event.value`** | Sanitising re-assigns `.value`, which fires `Changed` again; reading the live value makes the handler order-independent instead of depending on which `Changed` arrives first. |
| **`writer._render_entries` raises `ValueError` if any field contains a tab or a newline** | The roadmap's "the writer refuses to emit a field containing a tab". A backstop for any path that reaches the writer without going through a `TextField` — a future screen, a test, a caller not yet written. It is a programming error, not a user-facing one, so it raises rather than warning. |
| **`PromptDialog`'s plain `Input` is not covered here** | It is a filename prompt, not an entry field, and its validation is M2's #14. Recorded in *Out of scope* and picked up there. |

## Refinements made during implementation (2026-09-29)

Each of these replaces a decision above. They are recorded here rather than
edited into the tables silently, because each one is a judgement the dev may
want to overrule.

| Refinement | Why it changed |
| --- | --- |
| **#3 — `_render_tag`'s double-quoted branch also takes a tag with an apostrophe**, not only one with whitespace: the branches are (1) no whitespace and none of `"`, `'`, `\` → `#tag`; (2) no `"` and no `\` → `#"tag"`; (3) otherwise `shlex.quote`. | The rule as specced sent `don't` to `shlex.quote`, which emits `'#don'"'"'t'`. `#"don't"` round-trips just as correctly, is far more readable, and is **byte-identical to what the report's own reproduction already has in the file** — so the narrowest-form principle the decision was built on picks it. |
| **#6 — a value TOML can hold in a *literal* (single-quoted) string is still written as one**; only a value needing escapes takes the basic-string branch. | The plan asked for both "strings are written as TOML basic strings" and "byte-identical to today's output", which cannot both hold: `repr` emits single quotes. Python's `repr` and a TOML literal string agree exactly when the value has no `'`, no `\` and no control character, so that is the literal branch — and *every* config that works today is then byte-identical, not just formatted compatibly. Basic strings, with the full escape set the decision specifies, carry everything `repr` got wrong. This mirrors #3's narrowest-form rule rather than inventing a second philosophy. |
| **#15 — `TextField` sanitises through the reactive's own `validate_value` hook**, not through an `Input.Changed` handler that re-assigns `.value`. | Textual runs `validate_value` *before* posting `Changed`, so no listener ever sees an unsanitised value and there is no second `Changed` to order against — which is what the "read the live value, not `event.value`" decision was working around. It also covers a programmatic assignment as well as a keystroke or paste, and leaves cursor handling to `Input`. Entry's handler still reads the live value: harmless, and it keeps the handler independent of this mechanism. |

### Two behaviour changes #2's fix carries with it

Both follow from splitting the raw row instead of the stripped one. Neither is
in the report; both are locked by a test so they are visible rather than
latent.

- **Fields are stripped of spaces individually**, where `str.strip()` used to
  clean only the two outer edges of the row. `苹果<TAB> ping2guo3 <TAB>apple`
  previously parsed with the padding still attached to the middle field; it now
  parses clean. Strictly better, and what the decision above asks for.
- **A tab-indented triad row now reads as an empty first field.** A leading tab
  is either indentation or an empty `hanzi`, and it cannot be both; the empty
  field is what `writer.write` emits, and a tab-indented triad is not something
  the writer produces. Before this fix such a row **raised**, so nothing that
  worked is lost — but it is a real change and is asserted as such in
  `test_parser.py`. Space indentation is unaffected.

## Context

- **`parser.py`'s entry branch** guards on `raw_line.count("\t") >= 2` and then
  splits `stripped`, which is `raw_line.strip()`. The two disagree exactly when
  the row has an empty first or last field — that disagreement is finding #2.
- **`writer._render_tag`** quotes only when `any(ch.isspace() for ch in tag)`;
  `parser._parse_tags_line` reads the line with `shlex.split`. Nothing today
  makes the two agree on anything but the simplest tags.
- **`config._toml_lines`** writes every value with `!r`. Python's `repr` and
  TOML's string grammar agree on ASCII letters and little else: `repr("O'Brien")`
  is `"O'Brien"` (fine), `repr('O"B')` is `'O"B'` — a TOML *literal* string, in
  which the app then also emits backslashes unescaped.
- **`EntryScreen._create_category`** (`entry.py:461`) appends unconditionally.
  Its post-create block — add the leaf before the cursor, deferred
  `move_cursor`, set `_active_target`, `_clear_form`, `_apply_target_state`,
  notify, `_focus_first_field` — is the sequence the duplicate case reuses
  without the `deck.categories.append` and `save`.
- **`InspectTreeScreen._pending_deletes`** is a `list[NodeData]`, and `NodeData`
  is `(kind, path)`. Finding #1 is that nothing else is recorded and nothing
  re-checks the path. `action_rename`'s directory branch calls
  `data.path.rename(new_path)` with no awareness of the list.
- **The dev's own config** (`~/.config/idiomas/config.toml`) holds an absolute
  root and a name with no quote characters, so #6 and #7 are both latent rather
  than active for them. Both are reproduced against a temporary config path.
- The report's findings were reproduced against commit `aa11572`. Per
  `notes-sprint-6.md`'s first Assumption, each is **re-reproduced before being
  fixed** — the reproduction becomes the regression test, written failing first.

## Out of scope

- **Anything in M2 or M3.** In particular: markup escaping of the names this
  milestone validates (#16, M2), path-separator validation in Inspect Tree's
  prompts (#14, M2), and every compile-output finding (M3).
- **Surfacing the warnings this milestone produces.** #2's malformed-row
  warning and #3's unparseable-tag warning are *produced* here and discarded by
  every caller, exactly as every other warning is today. Connecting them to the
  UI is M9's whole deliverable.
- **A tag whose text begins with `#`.** Not round-trippable today, not in the
  report, and fixing it would change the storage format.
- **Renaming, deleting or reordering an existing category** from the app. Not in
  the report; Postponed in `notes-sprint-6.md` alongside in-app entry editing.
- **Validating `PromptDialog` input** — M2's #14.
- **Any change to the on-disk format.** Per `notes-sprint-6.md`'s third
  Assumption, nothing in this sprint changes it; every fix here makes the app
  agree with the format it already writes.
