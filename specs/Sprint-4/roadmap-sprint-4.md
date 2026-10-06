# Roadmap — Sprint 4

Sprint 3 made the app able to manage its own notebook. Sprint 4 is about the
app itself: how its screens are built, and how it gets installed. There are
fewer backlog items than in any sprint so far, but they're the densest. The
source is [`guidelines/backlog.md`](guidelines/backlog.md), written by the dev;
the decisions taken while turning it into this roadmap live in
[`guidelines/notes-sprint-4.md`](guidelines/notes-sprint-4.md).

The backlog's own terms are used below without further explanation:

- A **menu** is a screen whose content is a list to choose from (landing menu,
  notebook menu, Settings).
- A **screen** is what opens after choosing from a menu, when it isn't a menu
  itself (Entry, Browse, Inspect Tree).
- A screen is made of **panels**, the **content** inside them (trees, text
  fields, lists), and the **backpanel**: the screen itself, which holds every
  panel.

Milestones follow one ordering principle: **the classes before the screens
built from them.** The wizard is made of Textual screens, so it comes after the
rework that defines how a screen is put together. That rework is proven on one
screen (M1) before it spreads (M2). The small Entry fix waits for M1 because it
changes the same panel. The install work is split in three: plumbing with no
UI, then the wizard, then input methods, the riskiest macOS-specific part.

Each milestone lists its deliverable and the condition that closes it.

---

## M1 · Screen building blocks

The core of the backlog's *Classes rework*, proven on the screen the backlog
itself uses as its reference.

**Deliverable.**

- **Backpanel**, **Panel** and **text field** classes in the shared-widget home
  (`tui/screens/base.py`, or a package of its own — `plan.md`'s call), on the
  same "one place to change every X" basis as `SupaTree`, `FooterHint` and the
  dialog family. Panels and their content are separate classes: a tree or a
  field sits *inside* a panel and is not the panel.
- **Focus on entry.** Opening a screen focuses the *content* of its leftmost or
  topmost panel. Not the panel, not the backpanel.
- **`esc` goes up one level of nesting:** content → its panel → the backpanel.
  `esc` on the backpanel does nothing. It never leaves the screen; `q` does.
- **Panel movement is spatial and only works on panels.** shift+h/l move
  left/right and shift+j/k move down/up, following the actual layout, with no
  wraparound. They do nothing while content has focus: from a text field or a
  tree, `esc` to the panel first. This replaces `PanelAwareInput`'s shift+arrow
  shortcut out of a field.
- **Entry** is rebuilt on these classes. Apart from the intended key changes, it
  must look and behave exactly as before.
- [`../current/design.md`](../current/design.md): the navigation key table and
  its *Implementation* section are rewritten for the new model, and the
  menu / screen / panel / content / backpanel vocabulary is recorded there.
  [`../current/stack.md`](../current/stack.md) gets the architecture.

**Open for the spec conversation.** How focus gets *back in* from the backpanel
(shift+hjkl? `enter`? `tab`?). Whether menus are backpanel → panel → list, or
flatter. What "spatial" means when two panels only partly line up. And whether
Entry's panel movement from a tree with no target selected keeps today's
special case.

**Done when.** Entry opens with the tree focused; `esc` steps tree → panel →
backpanel and then does nothing; shift+hjkl move between panels only when a
panel has focus; the same holds from inside a form field; the dev confirms by
eye that Entry is otherwise unchanged; `design.md` documents the model; and the
full test suite passes.

---

## M2 · Every screen on the new classes

The rest of *Classes rework*, plus the backlog's *Browse fixes*, which the
backlog expects the rework to solve.

**Deliverable.**

- **Browse**, **Inspect Tree**, every **menu** and every **placeholder** are
  rebuilt on M1's classes and follow M1's focus / `esc` / shift+hjkl rules.
- **Browse fixes**, as the backlog states them: opening Browse focuses the
  filename filter (the topmost field), not the results list; `esc` in either
  filter field goes up to its panel, then to the backpanel. The old
  `AUTO_FOCUS = "#results"` workaround goes away. It existed only because a
  focused field used to trap `q`, and M1's `esc` fixes that.
- **Modularity pass.** The backlog invites broader improvements ("feel free to
  address possible improvements"). The candidates found in the code: the
  near-duplicate `build_tree`/`_add_dir_children` in `entry.py` and
  `inspect.py`, screen-specific CSS in `app.tcss` that should belong to the new
  classes (`#entry-form`, `BrowseScreen Input`), and the duplicated
  autocompile-worker code in `entry.py` and `inspect.py`. `plan.md` settles
  which of these land here. Nothing is refactored that isn't listed there.
- No screen still defines its own ad-hoc panel or focus handling outside the
  shared classes.

**Done when.** Every screen and menu opens focused on its first panel's
content; `esc` climbs the same way everywhere; shift+hjkl move spatially
everywhere; Browse opens on the filename filter and `esc` leaves it; the dev
confirms each screen by hand-testing; and the full test suite passes.

---

## M3 · New category on its own

The backlog's *Enter vocabulary fixes*.

**Deliverable.**

- Highlighting `(new category)` on Entry shows **only** a *new category name*
  field and **Create**. The hanzi, pinyin, translation and note fields are
  hidden.
- The name is **required**: Create does nothing with an empty (or
  whitespace-only) name.
- Create adds an **empty** category to the file and moves the cursor to it,
  where the normal add-word form takes over. Moving to the new node already
  works and is kept.
- **Compiling an empty category must not break.** Today `compile.py`'s
  `_render_table` would output a `longtable` with zero rows for it, which is a
  LaTeX error. Whether an empty category is left out of the PDF or shown as a
  bare heading is `plan.md`'s decision; failing to compile is not an option. A
  test covers the empty-category round trip through `parser.py`/`writer.py`.

**Done when.** A new category can be created with nothing but a name; an empty
name is refused; the cursor lands on the new category, ready for words; the
file compiles to a PDF with the empty category in it; and the full test suite
passes.

---

## M4 · Install groundwork

The non-UI half of the backlog's *Instalation wizard*: the backlog's "PATH?
Dependencies? Discuss.", plus everything the wizard will need to write to.

**Deliverable.**

- **PATH.** `idiomas` becomes a real command through a `[project.scripts]`
  entry. Brew packaging is out of scope, as the backlog says.
- **Nothing depends on the repo's location.** The config moves to
  `~/.config/idiomas/config.toml`. `compile.py`'s `templates/xecjk.tex` ships
  inside the package instead of being found by climbing up from `__file__`. The
  repo-root `PROJECT_ROOT` goes away.
- **New config schema:** user name, the registered languages, and per language
  its tree location and input methods. The old `.idiomas.toml` is **ignored,
  not migrated**.
- **Config-driven landing menu.** It lists the languages in the config instead
  of the hardcoded `LANGUAGES` constant. Chinese opens its notebook against its
  configured tree; German stays inert.
- **doctor, fixed and split.** It checks **Heiti SC** (M6 replaced Songti SC,
  and `doctor.py` still checks the old font), adds `macism` and `nvim`, and
  labels each check *required* (pandoc, xelatex, xeCJK, the font) or
  *optional* (`macism`, `nvim`).
- **Platform separation.** macOS-specific code — dependency checks, font paths,
  input-source switching, opening a PDF with `open` — moves behind one
  platform layer, so Windows and Linux can be added later without touching
  every call site. Only macOS is implemented.

**Open for the spec conversation.** How the app behaves with no config before
M5's wizard exists (an error message, a temporary prompt, or something else).
How templates are packaged (`importlib.resources` is the expected route). How
config writes stay atomic.

**Done when.** `idiomas` runs as a command from any directory; running it from
outside the repo finds the template and reads the config from
`~/.config/idiomas/`; the landing menu shows the languages from the config;
`idiomas doctor` reports Heiti SC, `macism` and `nvim`, each marked required or
optional; no module outside the platform layer calls a macOS-only tool
directly; and the full test suite passes.

---

## M5 · Installation wizard

The backlog's *Instalation wizard*, items 1–4.

**Deliverable.** A sequence of Textual screens, built on M1's classes, that
runs **only when no config exists** and never again once it has written one:

1. **Dependencies.** Runs M4's doctor. A missing **required** tool blocks the
   wizard from continuing and shows the exact install command. A missing
   **optional** tool shows a warning and lets the user carry on.
2. **User name.**
3. **Languages** — Chinese and German offered. Any number can be chosen.
4. **Tree location** per language, defaulting under `~/Documents/Idiomas/` and
   editable. The tree folder is created if it doesn't exist. An existing tree
   is used as it is, never overwritten. The dev points the wizard at their
   current tree; nothing is migrated automatically.

On finishing, the config is written and the landing menu opens.

**Open for the spec conversation.** How to move back and forth between steps,
and whether a step can be revisited. What happens if the wizard is quit
halfway (nothing written seems right). Whether choosing German creates its tree
folder even though German is inert. How a chosen location is validated
(writable, not inside the package).

**Done when.** With no config, launching `idiomas` opens the wizard; a missing
required dependency stops it; a missing optional one only warns; finishing
writes a config the app then runs from; relaunching skips the wizard; the dev
runs it fresh against their real tree and lands on a working Chinese notebook;
and the full test suite passes.

---

## M6 · Input methods

The backlog's wizard item 5, plus `postponedfeatures.md`'s *Macism input fix*,
which the dev brought in as its consumer.

**Deliverable.**

- **A wizard step, after tree locations,** that asks for each chosen language:
  for Chinese, the **hanzi** input method and the **translation** one; for
  German, the **German** input method and the **translation** one. The two
  answers may be the same.
- The options come from the input sources **enabled on the machine**, listed
  through the platform layer. If there's nothing suitable to pick, the user is
  told to add an input source in System Settings.
- **`input_method.py` reads the config.** Entry's hanzi field and the
  translation-side switch use Chinese's configured sources instead of Sprint
  2's hardcoded `SCIM.ITABC` / `USInternational-PC` pair. German's answers are
  stored and unused while German is inert.
- Everything Sprint 2 guaranteed still holds: a no-op off macOS, a no-op when
  `macism` is missing, and the switch runs in a worker thread.

**Open for the spec conversation.** How the entries from
`defaults read com.apple.HIToolbox AppleEnabledInputSources` map to the IDs
`macism` accepts: layouts and input modes are identified differently (see the notes'
Assumptions). Which language's input method is meant by "translation" on the
German side. And what the user sees when the list comes back empty: whether
"prompted to manually add them from settings" should re-check after they
return, or just explain and continue.

**Done when.** The wizard lists the dev's real enabled input sources; the
choices are saved; Entry's hanzi field switches to the chosen hanzi source and
back to the chosen translation source; changing those sources in the config
changes what Entry switches to, with no code edit; and the full test suite
passes.

---

## M7 · README and install

Added mid-sprint, during M5's spec conversation: the dev doesn't know the
deploy/packaging side of Python and asked how installation should actually
work for someone who isn't running this from a dev checkout. Not the
backlog's own item — the backlog only asks that "the minimal install will
hopefully be available via brew (this will not be added right now)" — but a
prerequisite the dev now wants settled this sprint, since the wizard (M5)
only matters once something has put `idiomas` on a user's `PATH` in the
first place.

**Rewritten on 2026-09-20**, at the start of the milestone's own spec
conversation. The original entry made `pipx` the install path and ruled out
any code change; the dev reversed both — "ignore the pipx thing, a git clone
makes me happy", and then "ideally it should be added to the path
automatically through the wizard". What the entry argued against `pipx` is
kept below, since the reasoning still stands for the options it rejected.

**Amended the same day**, after implementation: the wizard's first version
only *reported* a missing `PATH` entry, matching this entry's own "reported,
not silently fixed" line below. The dev asked "is this line mandatory? you
should check for it and add it" — it is mandatory, so the step now appends
the line itself, guarded against duplicating it on a second run. See
`requirements.md`'s Decisions table for the reversal in full.

**Deliverable.**

- **The README documents a `git clone` install**, spelled out step by step
  for a reader who doesn't know Python tooling: clone to
  `~/.local/share/idiomas`, create a virtualenv inside the clone, install
  the package into it, then run the app once by its full path to reach the
  wizard. The clone location is a suggestion, not a requirement — nothing
  has depended on where the code lives since M4.
- **The wizard puts `idiomas` on `PATH` itself**, as its final step: it
  symlinks the running console script into `~/.local/bin`, so every run
  after the first is just `idiomas`. This is the chicken-and-egg the README
  can't solve on its own — the wizard is only reachable by running the app,
  so the first run is by full path and the wizard fixes every run after it.
- **`~/.local/bin` not being on `PATH` is fixed automatically**, not just
  reported: the final step appends one line to the user's shell config
  (`~/.zshrc` by default), checked against the file's own contents first so
  a second wizard run never duplicates it. Nothing else in that file is
  touched. (Amended 2026-09-20, after the first implementation only
  reported the line — see below.)
- **The config is still written only at the end.** M5's rule — quitting
  before the last step writes nothing — now covers the symlink too: the
  final step creates the link, the tree folders and the config together.
- **A full README rewrite**, not just its install section. The file predates
  Sprint 3 and Sprint 4: it describes the old `source/` + `notebook/` two-tree
  model, invokes the app as `python -m idiomas`, links `mission.md` /
  `stack.md` / `roadmap.md` at the repo root, and knows nothing about the
  config, the wizard, Settings or Inspect Tree. A correct install section
  cannot sit inside a file the rest of which contradicts it.
- **`pipx` is not the documented path**, and neither is a neofetch-style
  `make PREFIX=... install` or a `curl | sh` installer. `make` fits a
  dependency-free single script and would still shell out to `pip` for a
  package with real dependencies (`textual`, `pypinyin`); `curl | sh` is for
  a prebuilt binary (PyInstaller, unscheduled build work) or for
  bootstrapping a package manager, neither of which applies here.
- No change to `doctor.py` (M4), to the notebook screens, or to the file
  format. The wizard (M5, M6) gains exactly one step.

**Open for the spec conversation.** Where the symlink's target comes from
when the app was started some other way than the console script. What the
step does when `~/.local/bin/idiomas` already exists, pointing somewhere
else. Whether the README documents `idiomas doctor`, given the wizard
already runs it.

**Done when.** The README's install section can be followed start to finish
by someone who has never used a virtualenv; following it produces a working
`idiomas` on `PATH` with **no manual `ln` or `PATH` edit at all** in the
common case; a second wizard run never duplicates the `PATH` line; the
wizard's new step is skipped cleanly when the link is already in place;
quitting the wizard before the end still writes nothing, symlink and shell
config included; and the full test suite passes.


---

## Not in this sprint

The dev's standing deferred list lives in their own `postponedfeatures.md` and
is theirs to manage. Its items not marked `(4)` stay out: the **Settings
submenu** (still all dummy items), **fixing `compile_all`'s renderer staleness
check**, **the PDF preview pane** in Inspect Tree, and **screen real estate**
(automatic scrollbars).

Also out, by decision during this sprint's planning:

- **A working German notebook.** German is registered and listed, but inert.
- **Installing dependencies for the user.** The wizard checks and blocks or
  warns; it doesn't run brew or tlmgr.
- **Brew packaging**, which the backlog itself defers. M7 documents `pipx`
  instead as this sprint's actual install path — brew stays a possible
  future addition, not a blocker for installing today.
- **Migrating the old `.idiomas.toml`.** The dev runs the wizard fresh.
- **Windows and Linux.** M4 keeps OS-specific code in one place so they can be
  added later; none is implemented.
