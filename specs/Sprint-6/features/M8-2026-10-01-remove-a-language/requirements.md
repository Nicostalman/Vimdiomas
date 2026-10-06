# M8 · Remove a language — requirements

## Anchor: the roadmap

From [`../../roadmap-sprint-6.md`](../../roadmap-sprint-6.md), *M8 · Remove a
language*:

> **Deliverable.**
>
> - **Settings › Remove a notebook removes a language**: drops it from the
>   config so it stops appearing on the landing menu and in Settings'
>   input-method list.
> - **Notes are never deleted without a separate, explicit confirmation.** The
>   language's `tree-<Language>` folder is a directory of the user's own files;
>   unregistering it and deleting it are two different intentions, and the
>   second is asked for separately through the app's existing `ConfirmDialog`,
>   whose `enter` is deliberately unbound.
> - **Removing the last language is handled**, not crashed into: the landing
>   menu with nothing on it has never existed.
> - **It takes effect in the running app**, same as M7's addition.
> - The option carries a legend description, per M4.
>
> **Done when.** The dev removes a language in the running app and sees it
> leave the landing menu without relaunching; their notes are still on disk
> unless they explicitly asked otherwise; re-adding it through M7 restores it;
> and the full test suite passes.

Source: [`backlog.md`](../../guidelines/backlog.md)'s *Implement remove a
notebook*: "The opposite operation, not much to add". The sprint notes settled
at sprint start that this means removing a **registered language**, not a file
(Inspect Tree's `d` already deletes files).

What earlier milestones left for this one (sprint notes):

- **M4:** options are `MenuOption`s, and *Remove a notebook*'s "Not available
  yet." description is replaced along with its behaviour.
- **M7:** an existing `tree-<Language>` folder is adopted untouched by *Add a
  language*. That is what makes "re-adding restores it" true here. Every menu
  rebuilds from the running config on screen resume
  (`MenuScreen.on_screen_resume`), keeping the highlight on the same option id
  and falling back to the first option when that id is gone. Adding saves a
  **copy** of the config before mutating the running one.

## Settled with the dev (2026-10-01)

| Question | Answer |
| --- | --- |
| Is deleting the `tree-<Language>` folder offered at all? | **Yes, as a second `ConfirmDialog`** after the removal itself is confirmed. Keeping it is the default: `n` and `esc` keep it. Deletion is permanent, the same as Inspect Tree's `d`. |
| Can the last language be removed? | **Yes.** The landing menu then lists only *Settings*, and *Settings › Add a language* is the way back. |
| The option's label | **Remove a language**, to match *Add a language* above it. The backlog's "Remove a notebook" is replaced in the UI, the README and `design.md`. |
| Does the language's input-method choice survive remove → re-add? | **No.** Removing drops the whole config entry. Re-adding goes through M7's form with fresh preselection; the notes come back, and the keyboard question is asked again. The config format does not change. |

## Agent decisions

Not raised with the dev: each follows from the roadmap, an earlier milestone's
decision, or the shape of the code.

| Decision | Why |
| --- | --- |
| **Compiled PDFs need no decision of their own.** | They live next to their `.md`, inside `tree-<Language>/` (`compile.notebook_path_for`), so they share the folder's fate. |
| **Compile-cache entries are kept with the folder and purged with it.** | The cache is keyed by absolute source path. Kept, they let a re-added language skip rebuilding files that haven't changed. With the folder gone they would be dead weight. They're harmless, since a missing PDF always rebuilds, but there's no reason to keep them. |
| **The config is saved before the folder is touched.** | If the save fails, the language stays registered and its folder intact. The opposite order could leave a registered language with no folder. |
| **A copy of the config is saved, then the running config is mutated**, as in M7. | A failed save can't leave the running app ahead of the file. |
| **The picker lists registered languages in config order**, including a name outside the registry. | It's the order of the landing menu. A hand-edited config can hold an unknown name, and removing one is a reasonable way to clean it up. |
| **`esc` on the folder question means "keep"**, not "cancel the removal". | `ConfirmDialog` dismisses `esc` as `False`, and the safe reading of `False` here is to keep the notes. Cancelling the removal itself is the first dialog's job. |
| **The folder question is skipped when the folder doesn't exist.** | There is nothing to ask about. The user may have moved or deleted it by hand. |
| **With no languages registered, *Input methods* and *Remove a language* show a placeholder** instead of an empty menu. | An empty `MenuScreen` already doesn't crash, but it reads as broken. M7 set the precedent with "Every supported language is already added." |
| **With no languages, the landing menu's *Settings* description changes** to "Add a language to start a notebook." | It's the only option on the screen, so its legend says what to do next. |

## Scope

### 1. Settings › Remove a language

- **The Settings option**: `MenuOption("Remove a language", "Stop using a
  language. Its notes are kept unless you ask.", id="remove_language")`,
  replacing the `remove_notebook` placeholder.
- **Choosing it** with at least one registered language pushes
  `RemoveLanguageScreen(MenuScreen)`. It lists each registered language in
  config order as `MenuOption(name, f"Remove {name}. You'll be asked about its
  notes.", id=f"language:{name}")`. With none registered, it pushes
  `PlaceholderScreen("There is no language to remove.")`.
- **Choosing a language** opens the flow in §2. The picker stays underneath
  until the flow finishes or is cancelled.

### 2. The removal flow

1. **First dialog** (`ConfirmDialog`): "Remove Italian from Idiomas? It leaves
   the main menu and Settings." `n`/`esc` cancels, and nothing changes. The
   user stays on the picker.
2. **Second dialog**, only if `config.tree_root(language)` is an existing
   directory: "Also delete {path} and the {N} files in it? This cannot be
   undone." `{path}` is the full folder path. `{N}` counts every file under it
   recursively, PDFs included ("1 file" in the singular, and "the empty folder
   {path}" when there are none). `y` deletes; `n`/`esc` keeps.
3. **Save** a copy of the config without the language, through `save_config`.
   On `OSError` or `ValueError`, an error-severity notification "Could not
   remove Italian: {exc}" appears. The running config is unchanged, the folder
   is untouched, and the user stays on the picker.
4. **Mutate** the running config: remove the language's `LanguageConfig` from
   `app.config.languages`.
5. **If deletion was asked for**: `shutil.rmtree(tree_root)`, then purge the
   compile-cache entries under it (§3). If `rmtree` raises `OSError`, the
   language stays removed, and an error-severity notification says "Italian
   removed, but {path} could not be deleted: {exc}". Whatever the deletion
   managed to remove before failing is gone; nothing is rolled back.
6. **Pop the picker** and notify on Settings:
   - folder kept: "Italian removed. Its notes are still in {path}."
   - folder deleted: "Italian removed, and its notes deleted."
   - no folder: "Italian removed."

Every message that quotes a path or a language name goes through `literal()`
or `markup=False` (Sprint 6 M2, #16).

### 3. The compile cache

`compile.forget_tree(tree_root: Path) -> None` loads the cache, drops every
key whose path is under `tree_root`, and saves it if anything changed. It is
called only after a successful deletion. A missing or corrupt cache is treated
as empty, as everywhere else.

### 4. Without relaunching, and with nothing left

- The landing menu and the Input methods picker already rebuild on resume
  (M7). After removing Italian, *Italian notebook* is gone from the landing
  menu, and the highlight falls back to the first option if it was on
  Italian.
- **Zero languages.** The landing menu lists only *Settings*, whose
  description becomes "Add a language to start a notebook." Settings ›
  *Input methods* shows `PlaceholderScreen("There is no language to set up.
  Add one first.")`, and *Remove a language* shows the placeholder from §1.
  *Add a language* works as in M7, and adding one brings the landing menu
  back.
- `idiomas compile` and `idiomas doctor` already handle an empty language
  list (nothing to compile; only `required` checks). They are covered by a
  test, with no code change expected.

### 5. Re-adding

Re-adding through M7's *Add a language* adopts the kept folder untouched
(`store.ensure_tree`). The notes reappear in the notebook, and the input
methods are asked again with fresh preselection. Nothing in M8 changes M7's
code path. A test drives remove → re-add end to end.

### 6. Docs

- `specs/current/design.md` › *Settings*: three entries, the third now
  **Remove a language**, with the flow above. "Remove a notebook is still a
  placeholder" is removed. The zero-language state is described.
- `README.md`: the Settings paragraph describes *Remove a language* and drops
  the "edit `config.toml`" workaround.
- `specs/current/stack.md`: `compile.forget_tree`, where the cache is
  described.
- `settings.py`'s module docstring.

## Out of scope

- **Remembering a removed language's input methods**: settled with the dev
  above.
- **Moving the folder to the Trash** instead of deleting it. Inspect Tree's
  `d` deletes permanently, and a platform trash API would be a new dependency
  per OS.
- **Deleting a single file or folder inside a tree**: that is Inspect Tree's
  `d`.
- **Renaming a language's folder or relocating the notes root**: nothing in
  the backlog asks for it.

## Context

- `ConfirmDialog` (`tui/screens/base.py`): `y` confirms, `n`/`escape` cancel,
  `enter` unbound. Callers use `push_screen(dialog, callback)`.
- `AddLanguageFormScreen._add` (`tui/screens/settings.py`) is the precedent
  for "save a copy, then mutate, then pop and notify".
- `MenuScreen.on_screen_resume` (`tui/screens/panels.py`) already handles a
  rebuilt list that lost the highlighted id, and an empty one.
