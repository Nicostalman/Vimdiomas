# M4 · The notebook menu — requirements

## Anchor: the roadmap

From [`../../roadmap-sprint-6.md`](../../roadmap-sprint-6.md), *M4 · The
notebook menu*:

> **Deliverable.**
>
> - **Inspect tree moves above Browse** in the notebook menu.
> - **One Compile, not two.** *Compile* and *Compile (force)* become a single
>   **Compile** that rebuilds what is stale and reports what it did. […] Force
>   stays available as `idiomas compile --force`, which already exists, and
>   deleting the cache is always safe.
> - **A legend line under every menu.** A dim italic line below the option
>   list showing the **highlighted** option's description, changing as the
>   cursor moves — not a static block, and not a suffix on the rows. Every
>   menu in the app gets it from the one shared `MenuScreen`: the landing
>   menu, the notebook menu, and Settings. *Browse* reads as "fuzzy-find a
>   file by name, or filter by tag"; the rest are written in the same voice.
> - `design.md`'s *Flat menus* section gains the legend as a standing
>   convention, stated once.
>
> **Done when.** The notebook menu reads Enter vocabulary / Inspect tree /
> Browse / Compile; every option on all three menus shows a description as it
> is highlighted; a rebuild after an in-app edit is picked up by the single
> Compile option; `design.md` states the convention; the dev confirms by hand;
> and the full test suite passes.

Source: [`backlog.md`](../../guidelines/backlog.md)'s *Main menu
modifications* section ("Move Inspect tree over Browse", "some sort of legend
in italics, maybe under the menu just like the keybindings cheatsheet", "the
two compiles only add noise").

## Already settled before this spec

From [`notes-sprint-6.md`](../../guidelines/notes-sprint-6.md)'s Decisions,
not reopened here:

- **The two Compile options merge into one called *Compile*, which rebuilds
  what is stale.** The backlog suggested merging under *Force compile*. The
  dev accepted the agent's counter-proposal at sprint start: the cached
  option only felt untrustworthy because of finding #11, which M3 fixed.
- **The legend is one dim italic line under the list showing the highlighted
  option's description.** The dev chose it at sprint start over an inline
  suffix and a static block.
- **The legend is a `design.md` convention.**
- **`main_menu.compile_summary(report)` stays the one place a Compile's
  results are worded** (M2/M3). It already says "Everything is up to date."
  when nothing was stale, and lists compiled files, failures and warnings
  otherwise. The merge leaves it unchanged.

## Scope

### 1. Notebook menu order and the single Compile

- The notebook menu (`MainMenuScreen`) has exactly four options in this
  order: **Enter vocabulary**, **Inspect tree**, **Browse**, **Compile**.
- *Compile* calls `compile_all(tree_root, force=False)` and pushes the
  existing results screen with `compile_summary(report)`. **What "stale"
  means, confirmed with the dev on 2026-10-01:** every Compile re-reads and
  re-parses **every** `.md` file in the tree and regenerates its
  intermediate markdown. Only the pandoc/xelatex step is skipped, and only
  for a file whose regenerated markdown and template match the stamp of
  its last PDF. That is how `compile_all` already works (M3's `_stamp_for`).
  An edit is therefore always picked up, whether it was made in the app or in
  Neovim. The dev asked whether "the button forces the parser as well", and
  it does. Running xelatex on files that haven't changed stays CLI-only.
- *Compile (force)* is removed along with its handler. No key on the menu
  forces a rebuild (dev, 2026-10-01). A forced rebuild stays CLI-only, as
  `idiomas compile --force`, which already exists and is unchanged.

### 2. The legend, on every menu

- **Every `MenuScreen` has a legend.** That covers the landing menu, the
  notebook menu, Settings, and **Settings › Input methods' language picker**
  (`InputMethodLanguagesScreen`). The picker is a fourth `MenuScreen` the
  roadmap did not name. The dev chose to include it (2026-10-01) because the
  convention says *every* menu.
- **Every option carries a description, and a missing one is an error.**
  Menus build their options as a `MenuOption`: an `Option` subclass whose
  constructor requires a `description: str`. `MenuScreen` refuses a plain
  `Option`, so a menu added later (M7, M8) cannot leave out its description
  by accident.
- **What the legend shows.** It shows the description of the option currently
  highlighted. It updates on every highlight change (`j`/`k`, arrows, mouse)
  and shows the first option's description when the menu opens.
- **Where it sits.** Directly below the option list, inside the backpanel,
  and centred with the list. It has the list's 40-column width and is indented
  to line up with the option text (dev, 2026-10-01). A one-row margin above
  it, beyond the list's own bottom padding, gives the two some air (dev,
  2026-10-01, after hand-testing).
- **Space is always reserved.** The legend is always **two lines** tall,
  whether the current description takes one line or two. Moving the cursor
  never shifts the menu. Every description must fit in two lines at the
  legend's text width, and a test enforces this.
- **Look.** Dim (`$text-muted`, like `FooterHint`) and *italic*.
- **Class.** `MenuLegend`, a subclass of `FooterHint` (dev: "consider
  recycling old classes"). It gets `FooterHint`'s muted look from the same
  `.footer-hint` rule and adds a `menu-legend` class for italic, width and
  the fixed height. It is never focusable.
- **Text is literal.** The legend renders its description through `literal()`
  (M2, #16). A landing-menu description includes a language name read from
  the config, and every user-derived string reaches a widget that way.

### 3. The descriptions

The dev accepted these drafts on 2026-10-01. The dev reviews the exact
wording on this spec, and any change is made here first.

**Landing menu** (`LandingMenuScreen`)

| Option | Description |
|---|---|
| *&lt;Language&gt;* notebook, functional | Add words, explore and compile your *&lt;Language&gt;* notes. |
| *&lt;Language&gt;* notebook, not yet functional (German until M6) | Not available yet. |
| Settings | Input methods, and adding or removing a language. |

**Notebook menu** (`MainMenuScreen`)

| Option | Description |
|---|---|
| Enter vocabulary | Add a word or a grammar point to a file, under a category. |
| Inspect tree | Walk your files: preview them, open in Neovim, rename, delete. |
| Browse | Fuzzy-find a file by name, or filter by tag. |
| Compile | Rebuild the PDFs of files changed since their last compile. |

**Settings** (`SettingsScreen`)

| Option | Description |
|---|---|
| Input methods | Choose which keyboard each language is typed with. |
| Add a language | Not available yet. |
| Remove a notebook | Not available yet. |

*Add a language* and *Remove a notebook* keep their placeholder description
until M7 and M8. Those milestones replace the description along with the
behaviour.

**Input methods picker** (`InputMethodLanguagesScreen`)

| Option | Description |
|---|---|
| *&lt;Language&gt;* | Change the keyboards used for *&lt;Language&gt;*. |

### 4. `design.md`

*Flat menus* gains a **Menu legend** subsection that states the convention
once:

- every menu option has a one-sentence description;
- the legend shows the highlighted option's description below the list;
- it reserves two lines;
- it is dim and italic;
- a menu added later must describe its options;
- descriptions use the same voice: an imperative or noun phrase, second
  person, ending with a full stop, saying what the option *does* rather than
  repeating its label.

*Settings* in `design.md` gets no new rule. Its placeholder list is unchanged
by this milestone.

## Out of scope

- **A key for a forced rebuild** in the TUI. It stays CLI-only, as above.
- **Changing what Compile reports.** `compile_summary` is unchanged.
- **Making the Settings placeholders real.** That is M7 and M8.
- **Updating a running menu when the code changes.** Menu options are
  static, so a change to their order or wording shows on the next launch, as
  it always has.
- **Legends on non-menu screens.** Entry, Browse and Inspect Tree keep their
  `FooterHint` keybinding cheatsheets as they are.

## Context

- No `MenuScreen` has a `FooterHint` today, so the legend has nothing to
  share space with.
- `.backpanel-flat VimOptionList` is 40 columns wide with `padding: 1 2`.
  The legend uses the same width and horizontal padding so its text lines up
  with the option text.
- Done-when's "a rebuild after an in-app edit is picked up by the single
  Compile option" is covered at the compile layer by M3's
  `test_compile_autocompile_revert_compile_rebuilds` (and its `_for_real`
  twin). This milestone adds the menu-level version: an edit made outside the
  autocompile path (as Neovim makes it) is rebuilt by the menu's one Compile,
  and a second Compile right after reports the tree up to date.
