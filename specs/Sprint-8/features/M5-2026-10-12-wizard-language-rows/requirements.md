# M5 · Language rows off the wizard's first step — requirements

## Anchor: the roadmap

> **Deliverable.** Step 1 (`DependenciesScreen`) no longer lists the checks that
> belong to a language (xeCJK and the CJK font): the list, its spinner during
> Recheck, and its column widths show only the `required` and `optional` rows.
> Nothing else changes: *Next*, *Install missing*, step 3's check and offer,
> Settings › Add a language, and `vimdiomas doctor` (which keeps listing them,
> labelled with their language) behave as before.
>
> **Done when.** On a machine where xeCJK is missing, step 1 shows no xeCJK or
> CJK-font row, *Next* works, ticking Chinese at step 3 still offers to install
> xeCJK, and `vimdiomas doctor` still lists it. The full test suite passes.

Source: the dev, 2026-10-12, after reinstalling on their own Mac: step 1 showed
`[ Chinese] xeCJK  missing` with no button that could fix it. Their request was
"remove it from the list". Not in `backlog.md`.

## Decisions

Settled with the dev in the spec conversation, 2026-10-12.

| Decision | Rationale |
| --- | --- |
| **Both language rows leave step 1**: xeCJK and the CJK font (`Songti SC` on macOS, `Noto Serif CJK SC` on Arch) | Dev's choice, over dropping only xeCJK, or showing them only once a language is chosen. They are the same kind of row; and step 1 comes before the language step, so it cannot know which languages will be ticked. |
| **`vimdiomas doctor` keeps listing them**, labelled with their language | Agent's recommendation, accepted. `doctor` is the full report and has no language step after it. |
| **Everything else is unchanged**: *Next*, *Install missing*, step 3's check and offer, Settings › Add a language | Dev's choice, over putting a note on step 1 in place of the rows. |
| **A row is a language row if its `Check.needed_for` is non-empty** | The field already says it, and `_installable_missing` already uses it for the same split. No new flag, no hardcoded names. |

## 1. What step 1 shows (`tui/screens/wizard.py`)

- The list shows the checks whose `needed_for` is empty, in `doctor.run()`'s
  order. Three places draw it and all three go through one filter: the first
  render (`_refresh_checks`), the spinner frames (`_render_pending`) and the
  render after a Recheck (`_apply_recheck`).
- `_checks_text` and `_pending_checks_text` do the filtering, so the name and
  label column widths are computed over what is shown. With the language rows
  gone, `[required]` is the widest label and the columns tighten; a CJK
  language's label (`[ Chinese]`) no longer sets the width.
- `self._checks` stays the full list. `_blocking` and `_installable_missing`
  already ignore a language row (`required` is `False` for them, and
  `_installable_missing` skips `needed_for`), so neither changes.
- Nothing new is shown in the rows' place: no note, no blank line.

## 2. What does not change

- `doctor.run()` and its checks, `doctor.label`, `doctor.missing_for`: the
  language rows still exist and are still checked.
- `vimdiomas doctor`'s output, and its exit status.
- Step 3's check when a language is ticked, and its offer to install
  (`tui/screens/dependencies.py`), and Settings › Add a language.
- *Install missing*: it already left the language rows to step 3.

## 3. Tests

- `tests/test_tui_wizard.py`:
  - `_checks_text` and `_pending_checks_text` omit a `needed_for` check; the
    first line still starts `[required] pandoc` and the widths are those of
    the rows shown.
  - The two existing tests that pin the language label on step 1
    (`test_checks_text_labels_a_language_check_with_the_language` and
    `test_checks_text_widens_the_label_column_for_long_language_lists`)
    are rewritten to say the opposite: the language row is absent. The label
    itself is `doctor.label`'s, and `tests/test_doctor.py` already covers it.
  - Pilot: with xeCJK missing (`_cjk_missing_checks`), step 1's rendered
    list has no `xeCJK` and *Next* still moves on; at step 3, ticking Chinese
    still offers the install. The existing tests that do this keep passing.
  - After Recheck the rows stay absent.
- `tests/test_doctor.py`: unchanged, and must pass. It already pins that `doctor`
  reports the language rows with their `needed_for`.

## 4. Docs

- `design.md`, *A language's missing dependencies*: the sentence "The wizard
  lists them at step 1 labelled with the language that needs them
  (`[ Chinese] xeCJK`, …) and they never block *Next* there" becomes: step 1
  does not list them (Sprint 8 M5); step 3 checks them when such a language is
  ticked and Settings › Add a language when one is added; `vimdiomas doctor`
  still lists them with the language as the label.
- `stack.md`: nothing. `doctor.label`'s doc string and `needed_for` stay true.
- Earlier sprints' specs are frozen and are left as they are.

## 5. Out of scope

- Any change to `doctor`, the install, or what the languages step does.
- Telling the user on step 1 that language dependencies are checked later.
- The pending Sprint 8 close, and Sprint 9.
