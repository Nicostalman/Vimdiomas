# M9 · Manual editing checks — validation

The acceptance bar for merging `2026-10-02-m9-manual-editing-checks`. It is the
roadmap's done-when, made checkable, against
[`requirements.md`](requirements.md)'s §1 format and §2 rule.

## Automated

- [ ] `pytest` passes in full.
- [ ] **No bogus grammar warnings:** a file under `Grammar/` with `###`
      subtitles walks with zero warnings; the same line in a vocabulary file is
      one warning. (The regression that made warnings unsurfaceable before.)
- [ ] **Every row of §2's *Reported* table is one warning**, with its line
      number and raw line: a markdown table, prose, YAML front matter, `####`,
      `## ` with no name, `###` outside a category, a stray `*note*` line, a
      row with too few fields, a row with a non-empty extra field, a row with an
      empty word, a non-`#tag` token in the tag block, a second `## Tags`, an
      unclosed quote in the tag block, a mismatched header, a missing header, a
      duplicate category name, a duplicate subtitle name.
- [ ] **Every row of §2's *Not reported* table is silent:** blank-line runs, no
      trailing newline, a note indented by two spaces or a tab, `## Tags`
      before the categories, an empty `## Tags`, tag order, an unquoted tag, a
      late-but-matching header, a trailing tab, an empty reading or
      translation, a duplicate entry.
- [ ] **The checks are additive:** for every file above, the deck, its tags and
      its `extra_fields` are exactly what they are on `main`, and the rendered
      markdown is unchanged. No existing PDF changes.
- [ ] **Both trees mark the file:** `<stem> ⚠` in Inspect Tree and Entry for a
      warned file, the bare stem for a clean one, `[b]x` still shown as typed.
- [ ] **The pane block:** for a warned file it heads the preview with
      `⚠ N warnings` and one `line N: message` plus indented raw line per
      warning, in MD mode only; a file-level warning shows with no
      line number; hidden for a directory, the root, a clean file and in PDF
      mode; eleven
      warnings show ten and `… and 1 more`; its content is a Rich `Text`.
- [ ] **A file the app cannot read** is still listed in the tree, with one
      warning saying so, and the screen opens.
- [ ] **MD mode's exit:** with a fake `nvim` that adds a category, the tree is
      rebuilt and the category is there; with one that adds a table, the marker
      and the block appear and exactly one warning notification is raised; with
      one that changes nothing, neither happens.
- [ ] **Changes inside the format are applied** (§3): a renamed category is
      Entry's create target after a remount, a moved entry lands in the other
      category's rows, reordering changes the markdown's order, an added tag
      reaches Browse's filter, and a renamed category rebuilds the PDF on the
      next Compile.
- [ ] **Nothing is blocked:** a warned file compiles, previews, opens, renames
      and deletes; Entry can create into it, keeping the hand edits; every line
      of it that does conform is in the deck.
- [ ] **Compile reports warnings for every file, rebuilt or skipped,** grouped
      under one path line with every message line indented; a warned file still
      lands in `compiled`.
- [ ] **`idiomas compile`** prints the warnings to stderr and exits **0**; with
      a genuine failure alongside, it still exits 1.
- [ ] **No new reads:** opening a tree screen parses each file once, as before.

## By hand (the dev)

In your own tree, with a file you can edit freely.

- [ ] **The lossy half.** In Inspect Tree, MD mode, `enter` on `Food.md`; in
      `nvim` add a markdown table, a fourth column on one row, and a line of
      prose under `## Tags`; `:wq`. On return: the file is marked `⚠`, the
      preview heads it with one warning per edit naming its line, and a
      notification gives the count. The PDF still rebuilds, with everything
      that does conform in it.
- [ ] `tab` to PDF mode with the cursor still there: the block is gone, the
      file keeps its `⚠` in the tree, and the rendered page fills the panel
      uncut. `tab` back and the block returns.
- [ ] **The lossless half.** Edit the same file again: break the blank lines up,
      indent a note by two spaces, move `## Tags` above the categories. On
      return there is **no** warning — it is a conforming file, untidily
      written, and the next entry you add through the app tidies it.
- [ ] **The good-faith half.** In another terminal, rename a category in
      `Food.md` and move a word into it. The running app shows nothing yet —
      expected. Open *Enter vocabulary*: the new name is in the tree and is a
      valid target, and adding a word to it keeps your edit. *Compile* rebuilds
      that file's PDF with the new heading.
- [ ] In MD mode's `nvim`, `:set expandtab?` says `noexpandtab`, and pressing
      `Tab` inside a row writes a real tab (`:set list` shows `^I`) — even with
      `expandtab` in your own config.
- [ ] Fix the lossy edits in `nvim` and `:wq`: the marker and the block are gone.
- [ ] *Compile* from the notebook menu with a warned file present: it is listed
      under *Warnings:*, grouped under its path, and the compile is reported as
      normal.
- [ ] `idiomas compile` in the terminal: the same warnings on stderr, `echo $?`
      is `0`.
- [ ] A German file too: add a third column to one row and see it warned
      (German rows are two columns).
- [ ] Nothing about a clean tree looks or behaves differently from before this
      milestone.
