# M4 · Unreadable notebook files — validation

The acceptance bar. Section numbers (§) refer to
[`requirements.md`](requirements.md).

## 1. Automated

- [ ] `uv run pytest` passes in full.
- [ ] Store tests: `read_source` on a readable, an undecodable and a missing
      file; `tag_index` with the bad file before and after the good one, never
      listing the bad one, and picking it up once fixed; `walk` and
      `ContentIndex` unchanged.
- [ ] Compile tests: `Bad.md` (`b'# Bad\n\xff\n'`) before `Good.md` gives one
      `failed` entry starting `could not be read:`, `Good.pdf` compiled, `Good`'s
      stamp saved, no stamp for `Bad`; a stamp earned before the file went bad
      survives; `compile_file` on it raises `SourceReadError`.
- [ ] CLI test: `vimdiomas compile` on that tree prints the failure to stderr,
      exits 1, prints no traceback, and still writes `Good.pdf`.
- [ ] TUI tests (Pilot, the app stays running after each): the notebook menu's
      Compile lists *Failed:* with the file and its cause; Browse's tag filter
      in filename mode and in content mode returns the good file's result with
      no notification; Browse `enter` and Inspect Tree PDF-mode `enter` on a
      bad source with no PDF notify `Compile failed for …` and open nothing;
      Inspect Tree's MD preview shows `Bad.md could not be read: …` with the
      `⚠` and warning block still present; renaming the bad file moves it,
      warns, starts no compile; Entry's entry, category and subtitle creation
      on a file that went bad notify and write nothing, keeping the form.

## 2. What the greps should find

- [ ] `git grep -n "read_text(encoding=\"utf-8\")" -- src/vimdiomas/store.py
      src/vimdiomas/compile.py src/vimdiomas/tui` prints only `read_source`'s
      own line, the compile cache's read (`_load_cache`) and no other notebook
      read. Anything else is either added to the spec or explained here.
- [ ] `git grep -n "Could not read" -- src` prints only the delete flow's
      `Could not read {name} — not deleted.` (a stat, not a source read).

## 3. By hand (the dev)

A scratch tree, not your notes. In `tree-<Language>`, make
`printf '# Bad\n\xff\n' > Bad.md` next to a valid `Good.md` carrying a tag, with
the config pointing at it. `Bad.md` sorts first.

- [ ] `vimdiomas compile`: stderr lists `Bad.md` with `could not be read: 'utf-8'
      codec can't decode byte 0xff …`, `Good.pdf` is written, the exit status
      is 1 (`echo $?`), and there is no traceback.
- [ ] The app, notebook menu › Compile: the results screen shows *Failed:* with
      `Bad.md` and its cause, and *Compiled:* with `Good.pdf`; `q` returns to the
      menu.
- [ ] Browse: type the tag of `Good.md` into the tag field in filename mode,
      then `tab` to content mode with a query that matches an entry in it: both
      show `Good`'s results, no error and no notification.
- [ ] Inspect Tree: `Bad` is marked `⚠`. In MD mode the preview reads `Bad.md
      could not be read: …` and the warning block is above it. In PDF mode,
      `enter` notifies `Compile failed for Bad.md: …` and opens no viewer.
- [ ] Inspect Tree: `r` on `Bad`, rename to `Worse`. The tree shows `Worse`, a
      warning says the title was left as it is, and no traceback.
- [ ] Entry: pick `Good.md`, then (in another terminal) `printf '\xff' >>
      Good.md` and create an entry in it: an error notification names `Good.md`
      and the cause, the form keeps what you typed, and nothing is written.
      Undo the stray byte afterwards.
- [ ] After each step above the app is still running.

## 4. Specs

- [ ] `design.md` and `stack.md` updated as §8 lists.
- [ ] Code and these three files agree.
