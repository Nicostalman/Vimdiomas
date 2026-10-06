# M4 · The notebook menu — validation

Grounded in the roadmap's done-when condition, made concrete.

## Automated

- `.venv/bin/python -m pytest -q` passes in full.
- **Order.** The notebook menu's options are exactly `Enter vocabulary`,
  `Inspect tree`, `Browse`, `Compile`, and no option's id is
  `compile_force`.
- **One Compile.** Selecting Compile calls `compile_all` with `force=False`,
  and nothing on the menu calls it with `force=True`.
  `idiomas compile --force` still forces (the existing `test_main.py`
  coverage, unchanged).
- **A rebuild after an edit is picked up.** The menu-level test from
  `plan.md` §2 covers a source edited on disk outside the app. M3's
  `test_compile_autocompile_revert_compile_rebuilds` (and `_for_real`)
  covers the autocompile path at the compile layer. Both pass.
- **Every option on all four menus has a legend.** The cross-menu test in
  `plan.md` §5 highlights each option on the landing menu, the notebook
  menu, Settings and the input-methods picker. It checks that the legend
  shows that option's description from `requirements.md` §3 and that the
  description fits in two lines.
- **The layout never shifts.** The legend is 2 rows tall, and the option
  list's region is identical, with a one-line description and with a
  two-line one.
- **The requirement is enforced.** A `MenuScreen` whose options include a
  plain `Option` raises `TypeError`.
- **Markup-safe.** A description containing `[b]x[/b]` renders verbatim.

## By hand (the dev)

Done when the dev confirms, in the real app on their own tree:

1. The notebook menu reads Enter vocabulary / Inspect tree / Browse /
   Compile.
2. Moving through each menu (landing, notebook, Settings, Settings › Input
   methods) with `j`/`k` changes the dim italic line under the list to the
   highlighted option's description, and nothing else on screen moves.
3. Edit a word in Inspect Tree's MD mode (Neovim) and return. Compile lists
   that file as compiled. Compile again and it reports *Everything is up to
   date.*
4. The wording of every description reads right.

## Docs

- `specs/current/design.md` has a *Menu legend* subsection under *Flat
  menus* stating the convention once, as in `requirements.md` §4.
