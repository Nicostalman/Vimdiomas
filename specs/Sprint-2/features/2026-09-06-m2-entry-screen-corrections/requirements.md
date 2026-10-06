# M2 · Entry screen corrections — requirements

Roadmap: [`../../roadmap-sprint-2.md`](../../roadmap-sprint-2.md#m2--entry-screen-corrections).
Proposals `#9`–`#16` (see [`../../guidelines/agent-notes.md`](../../guidelines/agent-notes.md)).

## Deliverable (from the roadmap)

- The form is inert unless the tree cursor sits on a valid target. Switching to
  the right panel off a leaf shows *choose a category* instead of editable
  fields.
- `(uncategorized)` appears under **every** file, not only files that already
  hold loose entries (reverses Sprint 1's M5.2).
- The tree root reads `[language] notebook`, not `source`. `Config` gains
  `language: str = "Chinese"`.
- No horizontal scrollbar under the tree; the view sizes to its content.
- The footer hint is rewritten for the M1 key map.
- A thinner input cursor than Textual's default block beam, applied to every
  `Input` in the app.
- The pinyin field is read-only and skipped by `tab` (hanzi → translation
  directly). The `_pinyin_touched` / `_last_prefilled_value` race guard is
  removed.
- `gloss` becomes `translation` in the UI only. `Entry.gloss` and the on-disk
  format keep the old name.

## Done when (from the roadmap)

- Twenty words still enter into one category without touching the tree.
- The right panel refuses focus off a leaf and says why.
- Every file offers `(uncategorized)`.
- `tab` never lands on pinyin.
- The root reads `Chinese notebook`.
- `tests/test_tui_entry_screen.py` passes as amended.

## Decisions made for this phase

1. **Inert-form presentation.** When the tree cursor is off a valid target
   (`VALID_TARGET_KINDS`), the form panel keeps its full five-field-plus-button
   layout, but:
   - the `#category-name` field (normally shown only for `new_category`) is
     replaced by a warning message — *"choose a category"* — occupying that
     same top slot;
   - all four remaining fields (hanzi, pinyin, translation, note) and the
     Create button are rendered but **disabled** (non-focusable, dimmed),
     not hidden.
   This mirrors the existing `new_category` layout (message/field in the top
   slot + fields below) rather than introducing a second layout shape.

2. **`Config.language` threading.** `EntryScreen.__init__` is changed to take
   the whole `Config` object (not just `source_root`), so it can read both
   `.source_root` and `.language`. This touches the call site in `app.py` that
   constructs `EntryScreen`. `Config` gains `language: str = "Chinese"` with
   that default, so existing `.idiomas.toml` files without the key keep
   loading — matches Sprint 1's config file being hand-authored/untracked.

3. **`gloss` → `translation` rename scope.** Renamed everywhere in the UI
   layer: the `Input` id (`#gloss` → `#translation`), `FIELD_ORDER`,
   placeholder text, the footer hint, `tests/test_tui_entry_screen.py`'s
   queries, and the local Python variable inside `_create_entry` (`gloss` →
   `translation`). `Entry.gloss` (the dataclass field) and the on-disk format
   are untouched — the local variable is still passed as `Entry(gloss=...)`.

## Context / constraints from other milestones

- M1 already owns all key-binding/navigation behavior (`NavigableScreen`,
  `PanelAwareInput`, `H`/`L` panel switching, `escape` defocus-to-panel). M2
  does not touch key bindings beyond the footer hint text and removing `tab`'s
  stop on pinyin.
- M1's `FormPanel` (the focusable right-panel container) and `escape` →
  `action_defocus_panel` behavior stay as-is; disabling fields must not break
  `escape`/`H`/`L` reaching the panel when a target is invalid — there's
  nothing focused to defocus from in that state, so it's a no-op, same as
  today for single-field panels.
- Sprint 1's `(uncategorized)` gating (`file_node.has_uncategorized`) is
  reversed per `agent-notes.md`'s *Inherited from Sprint 1* table — this
  touches `_add_dir_children` in `entry.py`, and whatever `store.py`/`walk()`
  computes for `has_uncategorized` may become unused if nothing else reads it
  (check before removing).
