# Design

The project's standing UX/UI guidelines: how the app behaves for the user —
navigation, keybindings, layout, and the conventions that apply across every
screen rather than to one feature. Its counterpart is [stack.md](stack.md), which
covers what the app is built with.

Cross-cutting conventions live here and are stated once. A milestone with a
user-facing surface is expected to follow them; when a milestone establishes or
changes one, this file is updated in place rather than the convention being
restated in that milestone's `requirements.md`.

## Supported platforms

Vimdiomas runs on **macOS** and **Arch Linux** (Sprint 8 M1). Arch derivatives
(Manjaro, EndeavourOS, Arch ARM: `ID_LIKE` lists `arch`) count as Arch, but only
`archlinux:latest` is tested. On any other system (another distro, Windows, the
BSDs, a Linux with no readable `/etc/os-release`) every command — the app,
`compile`, `doctor`, the wizard — prints one line to stderr and exits with status
1, before anything is written:

```
Vimdiomas runs only on macOS and Arch Linux. This is Debian GNU/Linux 13 (trixie).
```

The name is `os-release`'s `PRETTY_NAME`, else its `ID`, else the system's name.
There is no screen for it and no hint of what to install. `pip install` itself
is not gated. The gate checks the OS, never whether `brew` or `pacman` exist.

## Navigation conventions

A **menu** is a screen whose content is a list to choose from (the landing
menu, the notebook menu, Settings). A **screen** is what opens after choosing
from a menu, when it isn't a menu itself (Entry, Browse, Inspect Tree). A
screen is built from a **backpanel** (the screen itself, holding every
panel), **panels** (its bordered regions), and **content** — the focusable
things inside a panel: trees, text fields, buttons, lists. A panel and its
content are separate: a tree or a field sits *inside* a panel and is not the
panel (Sprint 4, M1 — the backlog's own terms, from *Classes rework*).

Established in Sprint 4 M1 on Entry, this model now covers every screen and
menu in the app (Sprint 4 M2): Browse, Inspect Tree, the three menus, and
placeholders. No screen defines its own ad-hoc panel or focus handling
outside the shared classes.

### Keys

| Key | On the backpanel | On a panel | On content |
|---|---|---|---|
| `esc` | Nothing | Focus the backpanel, **if reachable** (below) | Focus its panel |
| `enter` | Focus the first panel's content | Focus the panel's content | Unchanged: whatever the widget does (tree: select node; a button: press) |
| `H`/shift+`←`, `L`/shift+`→` | Focus the leftmost/rightmost panel's content | Move to the panel on the left/right, landing in its content | Nothing |
| `J`/shift+`↓`, `K`/shift+`↑` | Focus the bottommost/topmost panel's content | Move to the panel below/above, landing in its content | Nothing |
| `q` | Leave the screen | Leave the screen | Leave the screen, **except** in a text field, where it types |
| `tab` | Focus the first panel's content — same as `enter` | Focus the panel's content — same as `enter` | Screen-specific (Entry: next field, wrapping; a screen with modes: toggle the mode — see *Screen modes*) |

- **The "On content" `esc` row assumes a `Panel` to climb to.** A menu's
  content has none — see *Flat menus*, below, where `esc` does nothing
  instead.
- **A select field adds one rung between content and panel.** Its deployed
  list is content inside the field, so `esc` there collapses the list back to
  the field, and only a second `esc` — from the collapsed field — reaches the
  panel. See *Select fields*, below.
- **The backpanel is only reachable via `esc` with more than one panel.**
  With zero panels (a menu) or exactly one (Placeholder), there's nothing to
  gain by climbing there — no second panel to jump to, nothing else to see —
  so `esc` from the lone panel does nothing instead of reaching the
  backpanel. Entry, Inspect Tree, and Browse (M3, three panels) each reach
  it this way. `Backpanel.reachable()` is the single check behind this,
  used by both `Panel.action_defocus` and `Backpanel`'s own.
- **Spatial, no wraparound.** "The panel on the left" is the nearest panel
  whose region lies left of the current one, by edge distance; ties are
  broken by how close the two panels' centres are on the other axis.
  Likewise right/up/down. At an edge, the key does nothing. Neighbours come
  from the panels' actual on-screen geometry, not a per-screen list, so a
  stacked layout needs no extra code. From the backpanel, the same keys jump
  straight to the edge-most panel in that direction (leftmost, rightmost,
  topmost, bottommost) rather than to a neighbour, since there's no "current"
  panel to be relative to; ties break the same way as *landing on open* below
  (leftmost for a vertical jump, topmost for a horizontal one).
- **Only on panels and the backpanel.** H/J/K/L and shift-arrows act only
  when a panel or the backpanel **itself** has focus, never on content — a
  capital `H` typed while a panel's content has focus must not move panels,
  even when the content doesn't bind it itself (backlog: "I want the
  keybindings discussed (shift+jkhl) to work only when focusing the
  panels").
- **shift-arrows mimic H/J/K/L exactly**, including doing nothing on
  content: a tree gives up its own shift-arrow parent/sibling jump, and a
  text field gives up shift-arrow text-selection, while living inside a
  panel on this model.
- **`h`/`j`/`k`/`l`** (lowercase, unshifted) remain "whatever the arrow keys
  already do on that widget" — unchanged from the model below.

### Screen modes

A screen with modes switches between them with `tab` pressed from its
content — the one case the Keys table's `tab` row names beyond Entry's
own next-field cycling. The first mode is always the default, and the mode
is reset to it every time the screen opens: never persisted across a visit.
A badge names the current mode, red for the default and blue for the other
(Sprint 5 M4's convention). The footer hint always names what `tab`
switches *to*, not the mode that's active — the badge already says that.
Inspect Tree (PDF mode / MD mode, Sprint 5 M4) and Browse (filename mode /
content mode, M3) are the app's two screens with modes.

### Landing in content

"Land in a panel's content" (from shift+hjkl, from `enter` on a panel, or
when the screen opens) means: focus the panel's **first focusable, enabled,
visible content widget**. If it has none, focus the panel itself — this is
what happens on Entry when a directory or file is highlighted and every
field is disabled.

### Going in

`enter` goes one level in, the mirror of `esc`: on the backpanel, it lands in
the first panel's (leftmost, then topmost) content; on a panel, it lands in
that panel's content; on content, it's untouched (whatever the widget already
does on `enter`).

### On opening

A screen lands in its first panel's content — on Entry, the tree — never the
panel itself, never the backpanel (backlog: "when entering a screen, the
cursor should focus on the content inside a panel, not the panel itself, not
the backpanel").

### Select fields

A **select field** is a field whose value is picked from a list rather than
typed: it shows the current choice on one line, and `enter` deploys the list
below it (Sprint 4 M6, from the dev's own description of the input-method
question — "inside each field a list will deploy with all available input
methods and the user will be able to choose the corresponding").

- `enter` on the focused, collapsed field deploys the list and focuses it.
- Inside the list, `j`/`k` move and `enter` takes the highlighted option,
  which sets the value and collapses back to the field.
- `esc` collapses without changing anything — one rung up, to the field, not
  past it to the panel.
- The list opens on the current value, not at the top.
- Focus leaving the field or its open list collapses it, so a deployed list
  never hangs over the widgets below it.
- A field with nothing to choose from shows `(none available)` and does not
  deploy on `enter`; the screen asking the question says why and lets the
  user carry on rather than blocking on it.
- The collapsed line may show a shorter form of the label than the list does:
  the list is where the user needs every detail to tell two options apart,
  while the collapsed line already carries the field's own name in front of
  it and has a panel's width to fit in.

### Entry's grammar panel

A file under the tree's top-level `Grammar/` folder (Sprint 5 M5,
`store.is_grammar`) is entered through the same *Enter vocabulary* menu and
the same tree as every other file — the only visible difference is the form
on a category target, which gains a **Subtitle** select field between the
category-name field and the word field (Hanzi, for Chinese): `(none)`, the category's existing subtitles,
then `(new subtitle)`. Picking `(new subtitle)` reveals a name field right
below it, the same relationship `(new category)` has to its own name field
in the tree. `(uncategorized)` and `(new category)` show no Subtitle field,
on a grammar file or any other.

- Landing on a different tree target always resets the Subtitle field to
  `(none)` — it only ever holds a selection made on the *current* target.
- Creating an entry leaves the field on whatever subtitle it was just used
  with (a fresh subtitle included), so several entries go under the same one
  without re-selecting it each time.
- **Picking a Subtitle option moves focus onward**, one exception to a select
  field's general contract above (which "collapses back to the field"):
  `(none)` or an existing subtitle moves focus straight to the word field, and
  `(new subtitle)` moves it to the name field that appears — dev feedback
  after hand-testing, picking an option is a step forward in the form, the
  same as `Tab`.
- A vocabulary file's category never shows this field; nothing else about
  vocabulary changes.

### Screen real estate

Every `Panel` and `Backpanel` scrolls rather than clips (Sprint 5 M1). A
scrollbar appears only when a panel or backpanel's content overflows the
space it has, and takes no reserved gutter when it doesn't — a property of
`Panel`/`Backpanel` themselves, not a per-screen CSS rule or a hand-picked
height cap.

Whatever gains focus is scrolled into view automatically — `tab`-cycling
through a form, shift+hjkl moving between panels, or a screen landing focus
on open all bring the newly focused widget back on-screen if it was
scrolled out. This changes only what's *visible*: the focused widget's
identity never changes because it scrolled off-screen, and a scrollbar is
never itself a focus stop — shift+hjkl and `tab` skip over it exactly as
they do everywhere else in the panel model.

A tree's cursor line and a menu's highlighted option already scroll
themselves into view inside their own widget, independent of this — this
convention is about the *panel* around such a widget, or around a stack of
plain fields, not a replacement for it.

A panel too short to show even one full row of content just shows whatever
partial content fits, clipped — there is no enforced minimum panel height.

### Settings

The Settings menu has three entries. **Input methods** (Sprint 4 M6) lists
the registered languages, and choosing one opens the same two-field question
the installation wizard asks, prefilled from the config. Saving takes effect in
the running app, not just on disk. **Add a language** (Sprint 6 M7) lists the
registry languages the config doesn't hold yet — registered ones are hidden,
not shown disabled — and with none left says "Every supported language is
already added." Choosing one opens the wizard's input-method question for it
(`Add a language · Italian`, unfilled, so it preselects the way the wizard
does) and an **Add** button. Adding checks what the language needs (see *A
language's missing dependencies* below), creates its `tree-<Language>` folder
(an existing one is adopted untouched, so re-adding a removed language restores
its notes), saves the config and lands back in Settings with "Italian added."
The new language is on the landing menu, last before *Settings*, and in
Input methods without a relaunch: a menu rebuilds itself from the running
config whenever it is shown again, keeping the highlight on the same option.
**Remove a language** (Sprint 6 M8) lists the registered languages in config
order and asks twice, separately. The first dialog is "Remove Italian from
Vimdiomas? It leaves the main menu and Settings."; `n`/`esc` cancels and nothing
changes. The second, only if the `tree-<Language>` folder exists, asks "Also
delete {path} and the N files in it? This cannot be undone."; `y` deletes the
folder, `n`/`esc` keeps it, and keeping is the default, since the notes are the
user's own files and `enter` confirms neither dialog. The config is saved
before the folder is touched, so a failed save changes nothing. Settings
notifies "Italian removed. Its notes are still in {path}.", "Italian removed,
and its notes deleted." or "Italian removed.", and the language leaves the
landing menu and Input methods without a relaunch. Any language can be
removed, the last one included: the landing menu then lists only *Settings*,
described as "Add a language to start a notebook.", and Input methods and
Remove a language each show a placeholder until one is added.

The rule this sets, for whatever Settings gains later: a setting the wizard
asks for is a setting Settings can change, using the same widgets and the
same wording, so the two surfaces can't describe the same choice differently.
The wizard's input-method prompt is one constant both surfaces show.

### A language's missing dependencies

xeCJK and the CJK font are needed by a language, not by every install: a
German-only machine has no use for them. The wizard lists them at step 1
labelled with the language that needs them (`[ Chinese] xeCJK`, where
`[required]` and `[optional]` otherwise stand) and they never block *Next*
there; step 3 checks them when such a language is ticked, and Settings › Add a
language checks them when one is added. Both surfaces handle a missing one the
same way, through one shared helper:

- With a command for the platform: a confirmation says what is missing and
  what will run. `y` suspends the TUI, runs each command in the user's
  terminal so `sudo` can ask for a password, waits for Enter so the output can
  be read, then checks again. Only what the check finds decides: a command that
  failed, or one that never ran, is reported as the dependency still missing.
- With no command (a font nothing installs), or if
  declined, or still missing afterwards: the language is refused with a line
  naming what is missing and the command or message. Nothing is written.
- Only a language's own dependencies are ever offered for installation.

A check that can say *what* is missing (the LaTeX packages, Sprint 8 M2) does:
at step 1 its `missing` line is followed by the detail on the line(s) under it,
red, indented two spaces and wrapped to the panel, so the columns above keep
their alignment. The refusal words it `<name> missing: <detail>.`

### The focus look

*Accent = active, dim = rest.*

- The panel you're in — the panel itself focused, **or** content inside it
  focused — has an **accent** border. Every other panel is **dim**.
- The backpanel's border is **always accent, regardless of focus** — the
  one exception to the dim/accent convention (Sprint 4 M5 hands-on
  feedback: the backpanel is the only element where a focus change
  triggered no visible change of its own, since every panel going dim
  already communicates "focus left the panels" without the backpanel's
  border needing to do anything). It's always present at the same color,
  so focusing the backpanel never shifts the layout.
- Panel-focused vs. content-focused is shown by the content itself: a tree's
  cursor line dims when the tree loses focus; a text field's caret
  disappears.
- The border belongs to the **panel**, not to the content inside it — a tree
  or field inside a panel has no border of its own, so there's no double
  frame.

### Flat menus

A menu (the landing menu, the notebook menu, Settings) has no `Panel` at
all — its `OptionList` sits directly inside the backpanel, one level
shallower than every other screen. `esc` on the list does **nothing**,
same as `esc` on Browse's or Inspect Tree's one panel: with zero or one
panel there's no second panel to reach and nothing else to see, so
climbing to the backpanel gains nothing (see *backpanel reachability*,
above). `enter`/`tab` on the backpanel still focus the list, and shift+hjkl
are no-ops throughout, since there are no panels to move between — but in
normal use the backpanel is never actually reached, since `esc` doesn't
route there. The backpanel's border is always accent, same as everywhere
else — here, unlike a screen with real panels, the backpanel *is* "the
panel you're in," so there's nothing else to dim against it in the first
place. The list itself has no border of its own (the backpanel's is enough)
and gray padding on all sides so its background doesn't touch the
highlighted row's edge.

Browse (M3: three panels, stacked — query, results, and tag) is **not**
flat, and behaves like Entry and Inspect Tree here: `esc` from any
content reaches its panel, a second `esc` reaches the backpanel, and
shift+hjkl move between the three panels once one of them has focus.

Inspect Tree (Sprint 5 M4) has **two** panels — the tree and the PDF preview,
side by side — so it behaves the same way: `esc` from either panel's
content reaches that panel, a second `esc` reaches the backpanel, and
shift+hjkl move between the two panels once one of them has focus.

#### Menu legend

Every menu (the landing menu, the notebook menu, Settings, and Settings ›
Input methods' language picker) shows a **legend** below its option list
(Sprint 6 M4): the highlighted option's description, changing as the cursor
moves, and showing the first option's when the menu opens.

- **Every option is described.** A menu builds its options as `MenuOption`s,
  whose description is required, and `MenuScreen` refuses a plain `Option`.
  A menu added later must describe its options.
- **One sentence, one voice.** An imperative or noun phrase, second person,
  ending with a full stop, saying what the option *does* rather than
  repeating its label. A not-yet-built option says "Not available yet."
- **Two lines, always reserved.** The legend is two rows tall whether the
  description takes one or two, so moving the cursor never shifts the menu.
  A description must fit in two lines at the legend's text width (36
  columns).
- **Dim and italic,** the list's width and horizontal padding, so it lines
  up with the option text, with a blank row above it to set it apart from
  the list. It is never focusable.

Entry, Browse and Inspect Tree are not menus: they keep their keybinding
cheatsheet and get no legend.

### Browse

Browse (M3) is three stacked panels: a query field, the results panel (a
mode badge, the results list or an empty-state message, and the footer
hint), and a tag field at the bottom. Both modes share the one query field and the one tag
field — a mode toggle (`tab`) only ever changes the placeholder, the badge
and the footer hint, never the typed text, so switching mode mid-search
keeps what was typed and searches it in the other mode at once.

`enter` in a text field moves to the next panel down — query to results when
there are any, otherwise to the tag field; the tag field is the last panel, so
`enter` there does nothing — rather than opening or submitting anything, the
one departure from *Going in*'s "enter does whatever the widget already
does" for this screen's two fields.

In content mode, a result is one flat row: an entry's word (reading,
Chinese kinds only, with tone marks) and translation, or a category's or
subtitle's name alone in bold, with its location dimmed and aligned right. A row
that doesn't fit the list's width is cut with `…`, fields before location,
longest field first, down to one cell plus `…` each; the location is only
cut once every field is already at that floor, from its left so the
deepest part (the category) stays on screen. `enter` on any row opens its
file's PDF, compiling it first if it has none yet — the same action as
`enter` on a filename-mode row.

### Names the app refuses

Names are checked where they are typed, not where they are written, so the
user learns the answer before anything reaches the disk. The message is an
**error-severity notification**, the field keeps focus, and **nothing is
written** — the shape Inspect Tree has always used for a name it won't take
("`<name>` already exists.") rather than a new inline-error convention per
screen.

Only what actually breaks is refused. A name that merely looks risky, or that
differs from an existing one only in case, is a name the app can store and
read back, so it is accepted.

- **A category may not be called `Tags`** (Sprint 6 M1). `## Tags` is the
  heading the parser reads as the file's tag block, so a category by that
  exact name would write a heading nothing can ever read back. Matched
  case-sensitively: `tags` writes `## tags`, parses as an ordinary category,
  and is accepted.
- **A duplicate name selects what is already there** rather than being
  refused (Sprint 6 M1). Creating a category whose name the file already has
  moves the tree cursor onto the existing one, makes it the active target and
  says so — `"<name> already exists — selected."`, an ordinary notification,
  not an error. It writes nothing, and a second unreachable heading is never
  created. This is what creating a duplicate **subtitle** has always done, so
  the two creation paths no longer differ.
- **A file or directory name typed into Inspect Tree** — `r`, `n`, `m` —
  **must name a plain child of where it is created** (Sprint 6 M2). Refused:
  a name that is empty or only spaces; one that starts or ends with a space
  (refused, not trimmed, so the file is found under the name that was typed);
  one containing `/` or `\`; `.` and `..`; and any control character. So
  `../outside`, `sub/food2` and `a/b` are all refused, and nothing is moved,
  created or rewritten. Renaming a file into another directory is not
  something the app does; nvim and the shell do it.

  **The two lists differ on purpose.** A category name is heading text inside
  a file, so `Food/Drink` and `C:\new words` are legitimate categories, while
  both are impossible filenames. A file may be called `Tags`, which only
  matters as a heading.

### Text from the tree is shown as typed

A file name, directory name, category, subtitle, entry or the content of a
file is shown **exactly as it is on disk**, brackets included (Sprint 6 M2).
`[b]x.md` is listed as `[b]x`, not as a bold `x`, and `to [/] test` in a
translation is shown, not treated as styling. This holds everywhere such text
appears: trees, previews, select lists, Browse's results, dialogs and
notifications.

### Failures are reported, never fatal

Something going wrong with one file never ends the session (Sprint 6 M2):

- **Compile** lists what it compiled and then, under *Failed:*, each file that
  did not compile with the last lines of the error beneath it. The other
  files still compile and their PDFs still count as up to date; the next
  Compile retries only the failures. `vimdiomas compile` prints the same
  failures to stderr and exits with status 1.
- **A file that compiled, but not quite as written**, is listed under
  *Warnings:* below *Failed:*, the warning indented beneath it the same way
  (Sprint 6 M3). Today the only warning is a pinyin syllable printed without
  its tone mark. A warning is shown on every Compile while the file still has
  it, even when everything else is up to date. `vimdiomas compile` prints
  warnings to stderr and they do not change the exit status.
- **`Enter` in Inspect Tree's PDF mode** on a file with no PDF, when that
  file fails to compile, shows an error notification with the same error
  lines and opens no viewer.
- **`Enter` in MD mode without nvim** shows a warning naming the install
  command, the same shape as the preview pane's missing-poppler message, and
  the screen stays as it was.
- **A rename or creation the filesystem refuses** (permissions, a full disk)
  shows the OS's reason in an error notification; the tree is left as the
  disk has it.

### A file edited by hand is checked, never refused

The files are the user's, and a text editor is always a valid tool for them
(`mission.md`). So the app **reads a hand edit back and reports what it cannot
account for** (Sprint 6 M9). It never refuses a file, never rewrites a line it
did not understand, and never withholds a PDF: a warning is information.

**The standard is the format the app itself writes** — a `# Title` line, `##`
categories, `###` subtitles in a grammar file, rows of exactly as many
tab-separated fields as the language's kind has columns, a note as four spaces
and `*…*`, and one `## Tags` block last. The milestone's
`requirements.md` §1 writes it out in full.

**What is reported is what is lossy.** A deviation is shown when the text does
not reach the PDF as itself, or is read back as something other than what it
says — a markdown table or a line of prose (dropped), a fourth column (kept on
disk, never rendered), prose under `## Tags` (silently becomes tags), a row
with no word, a duplicate category name, a missing or mismatched header. A
deviation that is read back faithfully and tidied by the next in-app write is
**not** reported: a blank-line run, a note indented by two spaces, `## Tags`
placed before the categories, tag order. Adding a check means asking which of
the two it is, not adding to a list.

**Where it shows.**

- **The file is marked in every tree** that lists it — Inspect Tree and Entry —
  as `<stem> ⚠`, the marker dim and appended to the name, never mixed into it.
  A screen that lists files later is expected to carry the same marker.
- **The warnings are read in Inspect Tree's preview pane**, above the file's
  content, in **MD mode only** — in PDF mode the block would crowd the rendered
  page, so the mode shows the page and the file's `⚠` alone: a count, then each warning as `line N: message`
  with the offending line beneath it. A warning with no line to blame is shown
  without one. At most ten, then "… and N more".
- **Compile and `vimdiomas compile`** list them per file under *Warnings:*, as in
  *Failures are reported, never fatal*.
- **No count anywhere else.** No menu and no footer carries a total.

**When the app looks.** It does not watch the tree: a file changed in another
terminal is not noticed while the app sits still. It reads a file when a tree
screen is opened, when **MD mode's `nvim` exits** having changed it — the
moment a hand edit is picked up, where the tree is rebuilt, the preview
refreshed, the PDF recompiled and the warning count said in a notification —
when Entry writes, and whenever anything compiles.

**A change inside the format needs no detection.** Nothing in the app holds a
category name, an entry or a tag across a read, so a category renamed by hand
is simply what the file says the next time it is read. The app never compares
before and after.

### Fields sanitise what is pasted into them

Every text field replaces each control character in its value — a tab above
all — with a **single space**, as the value changes (Sprint 6 M1). A tab
pasted from a spreadsheet would otherwise be written straight into a
tab-separated row and shift its columns.

The user sees the result in the field immediately, before pressing Create:
nothing is altered at save time behind their back. A space rather than a
deletion, because the pasted `苹果<TAB>apple` is two words and deleting the
tab would glue them into one. One character for one, so the cursor never
moves under the typist. Leading and trailing spaces are left alone —
trimming as the user types would fight them mid-word.

### Inspect Tree's deferred deletes

`d` marks a deletion rather than performing one: the item disappears from the
tree at once, `u` undoes the most recent mark, and nothing is removed from
disk until the screen is left.

- **A rename carries any deletion marked underneath it** (Sprint 6 M1).
  Renaming a directory with a pending delete somewhere beneath it does not
  bring the deleted item back into the tree, and on leaving, the item goes at
  its new location. The rename is never refused for this reason: the deleted
  item is hidden, so refusing would name something the user cannot see.
- **The mark is on the file, not on its path.** A path that holds a different
  file by the time the screen is left is **left alone**, with a warning
  notification naming it — `"<name> changed since it was deleted — left
  alone."`. Not deleting is always the recoverable direction.
- **A path that is already gone is dropped silently.** There is nothing to do
  and nothing to report.

### Inspect Tree's PDF preview pane

The tree panel and a preview panel split the screen evenly (50/50). The
preview follows the tree's cursor — not just `enter`/selection — showing
whatever the highlighted node currently is — under its warnings, in MD mode,
when the file has any (see *A file edited by hand is checked, never refused*):

- **A directory (including the root)**: "Select a file to preview."
- **A file, MD mode**: the raw `.md` source text, matching what `Enter`
  opens in nvim in that mode. nvim is optional too: without it, `Enter`
  shows a warning with the install command and does nothing else (see
  *Failures are reported, never fatal*).
- **A file, PDF mode, no compiled PDF next to it**: "No compiled PDF for
  this file."
- **A file, PDF mode, no `pdftoppm` on `PATH`**: a message pointing at
  `brew install poppler` — poppler is optional, so this never blocks
  anything else on the screen.
- **A file, PDF mode, poppler present, terminal without kitty-graphics
  support**: the PDF's plain text (`pdftotext`), not a rendered page.
- **A file, PDF mode, poppler present, kitty-graphics support**: the actual
  rendered first page, via `pdftoppm` + the kitty graphics protocol —
  re-rendered on resize, fit inside the pane's current pixel dimensions
  while always keeping the PDF page's own aspect ratio (never stretched to
  fill the pane).

Rasterising and text extraction both run in a worker thread, cancelling any
stale in-flight one when the cursor moves again, so a fast cursor never
stalls the tree waiting on a render whose result would be thrown away
anyway.

## The compiled notebook

### Implementation

- `vimdiomas.tui.screens.panels.TextField` is the app's text field for screens
  built on the model above (`Input` with no `escape` binding of its own —
  it falls through to the containing `Panel` — and shift+left/shift+right
  overridden to a no-op, giving up `Input`'s own text-selection default so
  shift-arrows are inert on content like every other letter/shift-arrow
  pair). `vimdiomas.tui.screens.panels.Panel` is a focusable, bordered region:
  `focus_content()` finds the first focusable/enabled/displayed descendant in
  the screen's focus chain, falling back to the panel itself; its bindings
  (bubbled up from whichever content has focus) implement `esc`, `enter`/
  `tab` (both call `focus_content()`), and the spatial H/J/K/L + shift-arrow
  moves, all guarded to act only when the panel itself — not its content —
  has focus. A failed guard raises Textual's `SkipAction` rather than
  silently returning, so a screen with its own `tab` binding (Entry's
  field-cycling `action_next_field`) still sees the key once focus is on a
  field rather than the panel. `esc` on an already-focused panel only
  reaches the backpanel when `Backpanel.reachable()` says so. Both `Panel`
  and `Backpanel` mix in `vimdiomas.tui.screens.panels._ScrollsFocusIntoView`
  (Sprint 5 M1), which handles Textual's `DescendantFocus` event — bubbled
  to every ancestor of a widget that gains focus — by calling
  `scroll_visible()` on it, covering every way focus can land inside a
  panel or backpanel without a hook at each call site. `app.tcss`'s
  `.panel`/`.backpanel` rules set `overflow-y: auto`, Textual's own
  "scrollbar only on overflow, no reserved gutter otherwise" behaviour,
  replacing the old per-screen `height: auto`/`max-height` band-aids.
  `vimdiomas.tui.screens.panels.Backpanel` is the screen's single root
  container: it enumerates its panels, finds the edge-most one in a given
  direction (`edge_panel`, generalizing `first_panel`), and works out
  spatial neighbours from their on-screen regions (`neighbour`). Its own
  H/J/K/L + shift-arrow bindings call `edge_panel` directly (there's no
  "current" panel at the backpanel to ask `neighbour` about), guarded the
  same way as `Panel`'s. `reachable()` (`len(panels()) > 1`) is the single
  check that decides whether `esc` can ever focus the backpanel — used by
  `Panel.action_defocus` and by `Backpanel`'s own `action_defocus`, which
  also uses it for the flat-menu case (zero panels).
  `vimdiomas.tui.screens.panels.PanelScreen` is the screen base: it carries
  `q` (with the text-field guard), sets `AUTO_FOCUS = ""` so Textual's own
  auto-focus doesn't preempt it, and lands focus via `Backpanel.focus_content()`
  once the first layout pass has resolved regions (`call_after_refresh`). A
  subclass with its own `on_mount` must call `super().on_mount()` to still
  get this landing behaviour.
  `Backpanel.focus_content()` focuses the first panel's content — or, when
  there are no panels at all (a flat menu, below), the backpanel's own first
  focusable content directly, via the same descendant search `Panel`'s own
  `focus_content()` uses (factored onto a shared `_focus_first_content`
  helper). Its `enter`/`tab` and edge-jump actions guard on `self.has_focus`
  and raise `SkipAction` on failure, the same convention as `Panel`'s, for
  the same reason: a screen's own `tab` binding (Entry's field-cycling, or
  Inspect Tree's mode toggle) must still see the key once focus has moved
  past the backpanel onto real content.
  `vimdiomas.tui.screens.panels.MenuScreen` is the flat-menu base: a subclass
  implements `menu_options()` instead of `compose()`, and `MenuScreen`
  composes a `Backpanel` (tagged with the extra `backpanel-flat` CSS class —
  passing `classes=` to a widget replaces `DEFAULT_CLASSES` rather than
  adding to it, so `"backpanel"` has to be named again alongside
  `"backpanel-flat"`) holding one `VimOptionList` directly, no `Panel`.
  `LandingMenuScreen`, `SettingsScreen`, `InputMethodLanguagesScreen` and
  `MainMenuScreen` all subclass it.
  `vimdiomas.tui.screens.base.VimTree` carries `j`/`k` and the
  bordered/content-sized/no-horizontal-scroll look every tree in the app
  shares (`app.tcss`'s `VimTree` rule; `.panel VimTree` drops the border for
  a tree living inside a `Panel`, so there's no double frame).
  `vimdiomas.tui.screens.base.NoShiftArrowsTree(VimTree)` additionally
  overrides `Tree`'s own shift-arrow bindings (parent/ancestor/sibling
  jumps) to a no-op, for a tree living inside a `Panel`, which claims
  shift-arrows for panel movement instead — `EntryTree` and `InspectTree`
  both subclass it, the only two trees that live inside a panel.
  `vimdiomas.tui.screens.entry.EntryScreen` is the reference implementation:
  `PanelScreen` → `Backpanel` → a tree panel and a form panel, its tree an
  `EntryTree(NoShiftArrowsTree[NodeData])`, its fields `TextField`s.
  `vimdiomas.tui.screens.browse.BrowseScreen` has exactly three `Panel`s (the
  query field, the results with their empty-state, and the tag field, stacked
  in that order). `InspectTreeScreen`
  (below) has two.
- `vimdiomas.tui.screens.base.build_dir_tree` is the recursive `DirNode`/
  `FileNode` walk shared by Entry's and Inspect Tree's tree-building — the
  walk itself (add a directory node, recurse; add each file) was identical
  between the two, so it's written once and takes `make_dir_data`/`on_file`
  callbacks for the per-screen node-data and per-file-leaf differences (Entry
  adds category/uncategorized/new-category leaves under a file; Inspect Tree
  adds the file itself as a leaf).
  `vimdiomas.tui.screens.base.autocompile_one` is the shared worker-thread
  compile-and-notify-on-failure function, previously duplicated verbatim
  (apart from one word in the notify message) between `entry.py` and
  `inspect.py`.
- `vimdiomas.tui.screens.panels.SelectField` is the select field above: a
  focusable `Vertical` holding a `Static` display line and a collapsed
  `_SelectList(VimOptionList)`. `enter` is guarded on `self.has_focus` with
  `SkipAction` on failure, the same convention as `Panel`'s. The list binds
  `escape` to collapse rather than letting it bubble, which is what makes the
  extra rung work; the field itself leaves `escape` unbound, like `TextField`,
  so it falls through to the containing `Panel`. Collapse-on-blur is deferred
  with `call_after_refresh` and checked against `screen.focused`, since
  focusing the list is itself a blur of the field — where focus actually
  landed isn't settled until after the refresh. Both the field and the list
  check it, because focus can leave an open list without passing back through
  the field.
- `vimdiomas.tui.screens.panels.FormScreen` is the `PanelScreen` base for a
  panel holding several focusable widgets in a known order: a subclass lists
  them in `content_ids()` and `tab` cycles only those. Without it, Textual's
  default focus-chain cycling visits the `Panel` and `Backpanel` themselves
  as extra stops, both being focusable — the same bug `MenuScreen` guards
  against with its `tab` no-op. The wizard's steps and Settings'
  input-method screen both subclass it (extracted from the wizard's own
  `_WizardStep` in Sprint 4 M6, when the second caller appeared).
- `vimdiomas.tui.screens.input_methods` is the two-field input-method form
  itself — the choices, the labels, the preselection, and the advisory shown
  when there's little or nothing to choose from — composed by both the
  wizard's `InputMethodScreen` and Settings'
  `InputMethodSettingsScreen` so the two can't drift.
- `vimdiomas.tui.screens.base.VimOptionList` adds `j`/`k` to `OptionList`; used
  by every menu, by Browse's results list, and by `SelectField`'s deployed
  list.
- `vimdiomas.tui.screens.base.FooterHint` is the shared, muted, single-line
  keybinding reminder used at the bottom of a screen (`.footer-hint` in
  `app.tcss`), the same "one place to change every X" rationale as
  `VimTree` — introduced in Sprint 3 M4 when Inspect Tree needed one
  alongside Entry screen's existing one, and both were moved onto it rather
  than duplicating the style.
- `vimdiomas.tui.screens.base.ConfirmDialog`/`PromptDialog` are the app's
  standing modal-dialog family — one home for every yes/no confirmation and
  every single-field name prompt, per the same "one place" rationale as
  `VimTree`/`FooterHint` (Sprint 3, M5, introduced for Inspect Tree's
  delete/rename/create keys). Both are `ModalScreen` subclasses styled by the
  shared `.dialog` class in `app.tcss`: a small centered, bordered box over a
  darkened backdrop, with its `Static` content center-aligned too (a first
  pass that centered only the box, not the text inside it, read as
  off-center in manual testing). `ConfirmDialog` takes a message and
  dismisses with `True`/`False` — `y` confirms, `n`/`escape` cancel, and
  `enter` is deliberately left unbound so a destructive confirmation can
  never be triggered by the same key that submits everything else in the
  app. `PromptDialog` takes a label and an optional pre-filled value and
  dismisses with the submitted text or `None` (`enter` submits, `escape`
  cancels — an empty submission is the caller's job to treat as cancel, not
  the dialog's).
  `PromptDialog` uses a plain `Input`, not
  `vimdiomas.tui.screens.panels.TextField` — this modal has no `Panel` for a
  field to relate to, so the panel-model widgets have nothing to offer it.
  Callers push either with `self.app.push_screen(dialog, callback)` rather
  than awaiting, matching Textual's own modal-result convention.
- `vimdiomas.tui.screens.inspect.InspectTreeScreen` (Sprint 5 M4) wraps its
  `#inspect-panel` and a new `#preview-panel` in a `Horizontal`, each `width:
  50%`. `Tree.NodeHighlighted` (fires on cursor movement, unlike
  `NodeSelected`, which only fires on `enter`) drives `_update_preview`,
  which dispatches by the highlighted node's kind and the screen's PDF/MD
  mode to one of: a static message, a direct (synchronous) read of the `.md`
  source, or a worker. Workers run via
  `self.app.run_worker(..., thread=True, exclusive=True, group="preview")`
  — `exclusive=True`, unlike `autocompile_one`'s `False`, so a fast-moving
  cursor cancels a stale render rather than queuing it. A monotonic
  `_preview_generation` counter, bumped on every `_update_preview` call and
  captured by each worker's closure, is what actually stops a stale
  worker's result from landing after a newer one has already started — a
  cancelled `Worker` doesn't stop the underlying thread outright, so this is
  the real guard, `exclusive=True` only trims how many stay in flight.
  `vimdiomas.terminal.supports_kitty_graphics()` (env-var check, no I/O) and
  `vimdiomas.pdf_preview.pdftoppm_available()` (`shutil.which`) decide which
  branch runs; `vimdiomas.pdf_preview.RasterCache` (in-memory, keyed on PDF
  path + target pixel size, invalidated on the PDF's mtime) avoids
  re-rasterising a page the cursor revisits. `vimdiomas.tui.screens.inspect.
  PdfPreview(Static)` is a thin wrapper that reserves layout space and, on
  `show_image`, writes `vimdiomas.terminal.render_kitty_image`'s escape
  sequence straight to `self.app._driver` at the widget's own on-screen
  region — Textual doesn't composite raw terminal graphics itself, so its
  position is given explicitly by the caller (`_preview_content_region()`,
  `#preview-panel`'s own content region) rather than read off the image
  widget's own `region`: right after `display` flips from `False` to `True`,
  the widget's own region can still be the stale pre-layout one, while the
  panel — always displayed — never has this problem. The same region drives
  the target raster size. Resizing the screen (`on_resize`) re-runs
  `_update_preview` for whatever's currently shown, which re-rasterises at
  the pane's new size when that's the active branch. Pixel size comes from
  `vimdiomas.terminal.cell_pixel_size()` (a
  `TIOCGWINSZ` ioctl against `/dev/tty` — not `sys.stdout`, which Textual
  repoints to something with `fileno() == -1` while the app is running —
  falling back to a 10×20px assumed cell when the terminal doesn't report
  pixel dimensions either) multiplied by the preview panel's content region
  in cells. `pdftoppm` has no stdout mode (unlike `pdftotext`, which does):
  `rasterise_page` shells out to a temp file and reads it back rather than
  piping. It also does **not** compute an omitted `-scale-to-x`/
  `-scale-to-y` proportionally (checked against the installed poppler
  build) — the unset one just falls back to a default 150dpi resolution —
  so fitting inside a box while keeping the PDF page's own aspect ratio
  (never stretched) means computing both dimensions from
  `vimdiomas.pdf_preview.page_aspect_ratio()` (parsed from `pdfinfo`) and
  passing both, already matching, so `pdftoppm` has nothing left to stretch.
  A shown kitty image sits in its own layer above the text grid, entirely
  outside Textual's own repaint, so it has to be deleted explicitly
  (`vimdiomas.terminal.clear_kitty_images()`, the protocol's
  delete-all-placements escape) whenever switching to a message state and
  when actually leaving the screen. Textual unmounts a screen's children
  before calling the screen's own `on_unmount`, so clearing there is a
  silent no-op by the time it runs — `InspectTreeScreen.action_back_or_quit`
  clears it first, while `#preview-image` is still mounted, then calls
  `super().action_back_or_quit()`.

## The compiled notebook

A compiled PDF (`templates/xecjk.tex`) is as much a user-facing surface as
the TUI, and this is its standing look — established Sprint 5 M3, after the
TUI-only conventions above.

- **CJK face: Songti SC**, chosen by the dev from a rendered comparison
  against a reference image (`specs/Sprint-5/guidelines/image-1.png`) —
  their own eyeball call, not a match to the reference's own (sans) strokes.
  `vimdiomas.compile.CJK_FONT_NAME` is the single place this is named in code;
  everything else (`doctor.py`, the template) reads it from there or from
  the pandoc `cjkfont` variable it's passed as.
- **Latin face: Latin Modern Roman**, visually unchanged from before this
  milestone — named explicitly via `\usepackage{lmodern}` rather than left
  as an unstated fallback.
- **Title**: the document title set large and bold, flush with the left
  margin, followed by a thin horizontal rule — no author, no date, no
  article-class title-page spacing (a vocabulary list is one or two pages,
  not a paper).
- **Category headings** (`##` in the source, `\section` after pandoc's
  heading shift — corrected Sprint 5 M6, checked directly against pandoc's
  own raw output rather than assumed; this entry previously said
  `\subsection`, which the M6 template redefined without ever affecting a
  category heading, since it's not the command pandoc emits for one): large
  and bold, with breathing room above and below, no numbering (`secnumdepth`
  stays `-1`) — LaTeX's own default `\section` style already gives this
  look, so it's left unredefined. A clear break between one category's
  table and the next.
- **Margins, body size, row spacing**: 1in margins, 12pt body,
  `\arraystretch{1.6}` between table rows — all unchanged from before this
  milestone; reviewed alongside the above and kept as already right for a
  compact reference document.
- **Hanzi are set larger than the row's pinyin and gloss** — `\Large` against
  the 12pt body, the dev's own correction after the first pass looked too
  even between all three columns. Pinyin and gloss stay at body size.
- Applies to every compiled notebook — vocabulary today, grammar once
  Sprint 5 M6 adds its own renderer on top of this same template.
- **A grammar file's entry (hanzi, pinyin, translation, and its note if
  any) renders as up to four stacked lines, not columns** (Sprint 5 M6, `templates/xecjk.tex`'s
  `\HanziPinyin` macro plus `vimdiomas.compile._render_grammar_table`) — a
  second rendering path parallel to the vocabulary `longtable`, left
  untouched by this. Each hanzi character sits over its own pinyin syllable
  (or nothing, for a non-hanzi character like `...`), concatenated with no
  gap between characters so alignment holds regardless of word length.
  Pinyin is smaller than the body text (`\scriptsize` against 12pt) and a
  paler gray (`xcolor`), set close under its hanzi. A small gap separates
  pinyin from translation and a considerable one separates an entry from the
  next, so each entry reads as a unit — two module-level length constants,
  `GRAMMAR_PINYIN_GAP`/`GRAMMAR_ENTRY_GAP` next to `CJK_FONT_NAME`,
  first-pass values the dev eyeballs against
  `specs/Sprint-5/guidelines/image-1.png` like every other typographic
  constant in this section. A note renders as an italic parenthetical on its
  own line below the translation (vocabulary's gloss-note styling, but not
  inline). A subtitle (`###`, Sprint 5 M5) renders bold at body size,
  prefixed with an en dash, with no space of its own above it — the entry
  gap before it is the same as between two entries — clearly below a category heading
  (`\subsection`, the command pandoc's `###` actually shifts to — this
  redefinition is what the category-heading entry above used to,
  incorrectly, credit itself). Its beforeskip is negative, same convention
  as `\section`'s own default, so the paragraph right after a subtitle isn't
  left indented — a positive beforeskip was M6's first pass, caught in the
  dev's manual review; `_render_grammar_table` also prefixes its own output
  with `\noindent` rather than leaning on this alone, since a category or
  subtitle isn't the only thing a grammar entries block can follow
  (`deck.uncategorized` has none at all).
- **An alphabetical language (German, Sprint 6 M6) has its own, smaller look
  on the same template.** No CJK face is loaded at all (`xeCJK` is behind a
  conditional on the `cjkfont` variable), so every glyph is Latin Modern
  Roman. The vocabulary table is Chinese's minus the pinyin column: two
  columns, the word in `\Large`, then the translation with the note as an
  italic parenthetical, with the same column gap, row spacing and absence of
  rules. A grammar entry is Chinese's stacked unit minus the pinyin row: the
  word in `\Large` on its own line (`\GrammarWord`, a `\parbox` so a phrase
  that wraps is spaced by `\Large`'s own line height and does not collide),
  the same small gap, the translation, the italic note line, then the large
  gap before the next entry. `GRAMMAR_PINYIN_GAP` keeps its name: for German
  it is the gap after the word line. Chinese's PDFs are unchanged, pixel for
  pixel.
- **A vocabulary row too long for the aligned columns is an exception, in
  every language** (Sprint 6 M6). A word wider than 12em in `\Large` (ten
  hanzi, or twenty Latin letters), or whichever row makes the table wider than
  the text, is not put in the columns: it is set across the full width, the
  word in `\Large`, then the other cells after the usual 2em gap, and if that
  does not fit one line it wraps with the continuation lines indented by
  1.5em, so it reads as the same entry. The other rows are sized without it,
  so one German compound does not push every translation to the right. Widths
  are estimated by one function shared by every kind (`compile.py`), and a
  table that fits is rendered exactly as before. A grammar entry's head line
  can break between units, so a long Chinese phrase wraps.
