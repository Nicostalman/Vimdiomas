# M2 · Entry screen corrections — validation

Acceptance bar for this branch, grounded in the roadmap's **Done when**
condition ([`../../roadmap-sprint-2.md`](../../roadmap-sprint-2.md#m2--entry-screen-corrections)).

## Automated

- `uv run pytest tests/test_tui_entry_screen.py -v` (or the project's usual
  test invocation) passes with the amendments from plan.md §10:
  - `#translation` queries replace `#gloss` throughout.
  - A case asserting fields are disabled and the warning is shown when the
    tree cursor sits on a `dir`/`file` node (not `category`/`uncategorized`/
    `new_category`).
  - A case asserting fields re-enable and the warning hides on moving the
    cursor onto a valid target.
  - A case asserting `(uncategorized)` appears for a file with zero loose
    entries.
  - A case asserting the tree root label is `f"{language} notebook"` given a
    `Config` with a non-default `language`.
  - A case asserting `tab` from the hanzi field focuses translation, not
    pinyin.
- Full suite (`uv run pytest`) still passes — no regressions in
  `test_tui_navigation.py` or other M1-era tests from the disabled-field
  changes touching focus handling.

## Manual / hand-testing

1. **Twenty words, one category, no tree touch** (Sprint 1's original bar,
   must still hold): open the entry screen, land on a category leaf, enter 20
   words in a row without touching the tree — all save correctly.
2. **Inert form off a leaf**: move the tree cursor onto a `dir` or `file`
   node. Confirm: the top slot shows a "choose a category" message, the four
   fields and Create button are visibly disabled, and `tab`/click cannot focus
   them.
3. **Every file offers `(uncategorized)`**: open a file in the tree that has
   never had a loose (uncategorized) entry — the `(uncategorized)` leaf is
   present under it.
4. **Tree root label**: with `.idiomas.toml` unset (or explicitly
   `language = "Chinese"`), the tree root reads `Chinese notebook`. Change the
   config value and confirm the label follows it on next launch.
5. **No horizontal scrollbar**: with a long category or file name in the
   notebook, the tree panel does not grow a horizontal scrollbar; it sizes to
   its content (wraps, truncates, or expands per whatever plan.md §8 lands
   on — confirm the chosen behavior looks right, not just "no scrollbar").
6. **Footer hint**: reads correctly for the current key map (`H`/`L`,
   `escape`, `tab`, `enter`) with no stale references to removed bindings.
7. **Thinner cursor**: every `Input` in the app (entry screen fields, browse
   screen's filter field) shows a visibly thinner cursor than Textual's
   default block beam.
8. **Pinyin read-only**: typing hanzi still auto-fills pinyin; clicking or
   tabbing into the pinyin field does not allow typing; `tab` from hanzi
   lands on translation directly, skipping pinyin.
9. **`gloss` → `translation` UI-only**: the field is labeled/placeholder
   "Translation" in the UI; inspect a saved entry on disk (or `Entry.gloss` in
   code) to confirm the on-disk field name and dataclass attribute are
   unchanged.

## Merge bar

All automated cases above pass, and the manual walkthrough (1–9) is run once
against a real notebook before the branch is proposed for merge — per the
project's standing practice of hand-testing before considering a milestone
closed.
