# M2 · Curly-quote spacing — validation

The acceptance bar for the branch. Section numbers (§) refer to
[`requirements.md`](requirements.md). Checks marked **auto** are tests in the
suite. The rest are run once and reported.

## 1. The quote rule (auto, unit)

The function of §3, for each input, gives:

| Field | Result |
| --- | --- |
| `a "b" c` | `a “b” c` |
| `"b" c` | `“b” c` |
| `("b")` | `(“b”)` |
| `say "hi."` | `say “hi.”` |
| `a-"b"-c` | `a-“b”-c` |
| `a "b"` | `a “b”` |
| `a “b” c` (typed) | unchanged |
| `it's` | unchanged: `'` is not touched |
| `他说"你好"再见` | `他说“你好”再见` |
| `他说"你好` | `他说“你好` |
| `你好" a` | `你好” a` |
| `"` alone | `“` |
| `` (empty) | empty |

And, through the renderer:

- [x] A vocabulary entry with `a "b" c` in the word, the translation and the
      note gives `“b”` in all three, for both kinds, and the LaTeX escaping of
      `\ & % $ # _ { } ~ ^` is unchanged beside it.
- [x] A grammar entry whose word is `他说"你好"` puts `“` after `说` and `”`
      after `好`, each in its own `\HanziPinyin`.
- [x] An entry with no `"` renders to exactly the markdown it did before.

## 2. The PDF (auto, integration)

Needs pandoc, xelatex and `pdftotext`. Each skips when `pdftotext` is missing.
"Token" is a word box from `pdftotext -bbox`. Two tokens are separate when a
space or a gap divides them.

Chinese:

- [x] A heading `a "b" c`, a file whose name is `a "b" c`, a category `a "b" c`
      and an entry translation `a “b” c`: each prints the tokens `“b”` and `c`,
      and none prints `“b”c`. The heading and the title are the roadmap's
      done-when case.
- [x] A heading `a -- b` and one `a --- b`: the dash is a token of its own, and
      `b` is another.
- [x] A heading `a ... b`: the text holds `…`, and does not hold `⋯`. (Poppler
      runs the Latin `…` into its neighbours, in plain LaTeX too, so the glyph
      is what is checked and not a gap.)
- [x] An entry translation `一，二。 b`: the space after `。` is kept, and `b` is a token of its own. A space before a hanzi is not specified (see `requirements.md`).
- [x] **Genuine quotes are not touched.** A heading `他说“你好”再见` and an
      entry translation `他说“你好”再见` each remain a single token. No gap
      before or after the quotes.

German:

- [x] An entry `a "b" c` prints `“b”` and `c` as separate tokens, and the first
      quote is the opening glyph.
- [x] A heading `a "b" c` still prints as it did.
- [x] Template: the patch's lines sit between `$if(cjkfont)$` and `$endif$`
      (auto, structural).

## 3. Measured once, by the agent

Reported in the hand-off. These are the evidence the spec's *What was measured*
already records, rerun on the final template.

- [x] **Identical layout.** `他说“你好”他说，说“你好”他说。她说‘你好’了——好的。`
      compiled with and without the patch gives identical `pdftotext -bbox`
      output.
- [x] **The guard.** A scratch template whose patch names a macro that does not
      exist compiles, and the space is swallowed as before. The real template
      keeps it.
- [x] **A wrapped heading.** A Chinese heading longer than 72 columns, with `，`
      and `”` inside it, compiles to identical `pdftotext -bbox` output whether
      or not pandoc wraps its LaTeX, so no `--wrap=none` is needed.
- [x] **Linux.** The integration tests run in `docker/`'s Arch container and
      pass. Or: Docker is unavailable, and the dev has been told.

## 4. The dev's own check

- [ ] Compile the real Chinese notebooks. Every PDF rebuilds (the template
      changed). The dev looks at a heading or two with quotes, dashes or an
      ellipsis, and at an entry with a quote. The only visible differences from
      before are the restored spaces, `…` in place of `⋯`, and entry quotes
      curling. The dev confirms by eye.
- [ ] Compile the German notebook. Every PDF rebuilds, and looks the same
      except for an entry that contains a `"`, whose quotes now open and close.
- [ ] A genuine Chinese quote in a notebook, if the dev has one, looks as it did.
- [ ] The source `.md` files are untouched: `git status` in the dev's tree
      shows no change, and a typed `"` is still a `"` in the file.

## 5. Merge bar

- [x] The full suite passes, integration tests included (1269 passed). The
      project has no lint configured.
- [x] `plan.md`, `requirements.md` and `validation.md` match the code.
- [x] `specs/current/stack.md` carries the note.
- [x] The dev said M2 is finished by asking for the merge (2026-10-03). The
      agent did not see §4's checks reported, so they are left unticked above.
