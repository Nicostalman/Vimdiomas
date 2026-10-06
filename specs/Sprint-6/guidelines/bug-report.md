# Idiomas bug review — 2026-09-29

Reviewed commit: `aa11572eb709fe0c1aa702f1d0071fb98d92f200`.

Found **19 reproducible bugs: 2 high priority, 13 medium priority, and 4 low priority**. Findings 1–10 come from the first review pass, findings 11–19 from a second pass over the same commit. The most serious issues can delete the wrong file or persist an entry that prevents the notebook tree from reopening.

This is a report only. No application code, existing tests, configuration, or specifications were edited. The reproductions used temporary files and headless UI sessions.

## Validation and scope

- Reviewed the Python application, including parsing/writing, discovery, configuration, installation, platform adapters, pinyin, compilation, terminal/PDF preview support, and TUI screens; cross-checked relevant tests and specifications.
- Ran `.venv/bin/python -m pytest -q`: **696 passed, 2 warnings in 128.42 seconds**, including the existing PDF integration tests. Both warnings concern deprecated `codecs.open()` usage in pypinyin.
- Ran additional probes through the existing functions and Textual's headless test harness. These reproduce cases missing from the passing suite.
- The second pass (findings 11–19) used the same method: every finding was reproduced with a headless Textual session, a direct call into the existing functions, or a real Pandoc/XeLaTeX compilation. Anything stated only from reading the code is marked as such.
- Environment: macOS, Python 3.14.7, Textual 8.2.8, pypinyin 0.55.0; Pandoc, XeLaTeX, and Poppler available.
- Real Linux desktop/input-method behavior and graphical terminal rendering were not exercised. Passing tests and this review do not establish that every possible bug has been found.

Priority meanings: **P1** — address first because of data loss or blocked core workflows; **P2** — a specific supported input or workflow fails; **P3** — output correctness with limited impact.

## Findings

### 1. [P1] Renaming a parent directory leaves pending deletes pointing at the old path

**Location:** `src/idiomas/tui/screens/inspect.py:469–474`, with deletion at lines 226–235.

Pending deletions store paths. Renaming a directory moves its contents immediately but does not update pending deletion paths beneath that directory. Rebuilding the tree makes the supposedly deleted file visible again. Leaving the screen then acts on the obsolete path.

**Reproduction:**

1. In Inspect Tree, delete `Old/DeleteMe.md` and confirm. Stay on the screen so the deletion remains pending.
2. Rename directory `Old` to `New`.
3. The file reappears at `New/DeleteMe.md`.
4. Recreate `Old/DeleteMe.md` with different content before leaving Inspect Tree.
5. Leave the screen.

**Observed:** the original file at `New/DeleteMe.md` survives, while the replacement at `Old/DeleteMe.md` is deleted. Confirmed with a headless UI reproduction; the replacement was created directly in the temporary filesystem. Creating the replacement through the UI is also permitted because the old path is now free.

**Suggested fix:** remap pending descendant paths when a directory is renamed, or block that rename while descendant deletions are pending. Verify the pending item is still the intended file before committing destructive operations.

**Regression coverage:** delete → rename ancestor → leave; additionally reuse the old path and verify its replacement survives.

### 2. [P1] An entry without a translation is saved but cannot be parsed again

**Location:** `src/idiomas/parser.py:82–84`; entry validation at `src/idiomas/tui/screens/entry.py:369–377` and the grammar entry creation paths.

The entry form only requires hanzi. It can save a row such as `你\tni3\t`. The parser counts tabs in the original line but splits `stripped`, which has already lost the trailing tab. Unpacking then fails.

**Reproduction:** select an entry target, enter `你`, leave Translation empty, and press Create. Confirmed that the form writes the entry; parsing the saved file raises:

```text
ValueError: not enough values to unpack (expected at least 3, got 2)
```

**Impact:** subsequent entry creation, opening either tree screen, and compilation can fail until the source file is repaired. Those screens parse every source file while constructing the tree, so one such row can block the whole tree view.

**Suggested fix:** split the original tab-delimited row without removing empty boundary fields. If translations are required, also validate them before saving. A malformed row should produce a diagnostic rather than crash tree discovery.

**Regression coverage:** save/reload empty translation, whitespace-only translation, and empty leading/trailing fields; exercise both vocabulary and grammar forms.

### 3. [P2] Saving a valid quoted tag can make the source file unreadable

**Location:** `src/idiomas/writer.py:16–19`; tag parsing in `src/idiomas/parser.py:6–7`.

The parser uses shell-style quoting, while the writer only quotes tags containing whitespace. It does not escape apostrophes, double quotes, or backslashes consistently with that parser.

**Reproduction:** a valid Tags section containing `#"don't"` parses to the tag `don't`. Running the parsed deck through `write()` produces `#don't`. Parsing that output raises `ValueError: No closing quotation`.

**Impact:** adding an otherwise normal entry rewrites the entire deck and can corrupt its existing tag syntax. Subsequent discovery, tag filtering, and compilation fail on that file.

**Suggested fix:** serialize tags with quoting and escaping compatible with `shlex.split`, and handle invalid tag syntax as a parse warning instead of an uncaught exception.

**Regression coverage:** parse → write → parse for apostrophes, double quotes, backslashes, and whitespace in tags.

### 4. [P2] Automatically generated pinyin can crash compilation

**Location:** `src/idiomas/pinyin.py:33–56`; compile error handling at `src/idiomas/tui/screens/base.py:79–87`.

The tone renderer requires one of its supported vowels for every non-neutral syllable, but `guess()` can produce syllabic consonants.

**Reproduction:** with the installed dependency versions:

```text
guess("嗯") -> "n2"
to_tone_marks("n2") -> ValueError: no vowel to mark in syllable 'n'

guess("呣") -> "m2"
to_tone_marks("m2") -> ValueError: no vowel to mark in syllable 'm'
```

**Impact:** these characters are accepted and saved by Entry, whose pinyin field is read-only, but the PDF renderer cannot process them. The resulting `ValueError` also bypasses the autocompile helper's exception handler, which only catches subprocess and OS errors.

**Suggested fix:** support syllabic consonants generated by the pinyin dependency and provide a safe fallback/diagnostic for unsupported syllables. Ensure render errors are reported without terminating the TUI.

**Regression coverage:** run guessed pinyin through both PDF rendering modes for `嗯` and `呣`, and test the worker's render-error path.

### 5. [P2] Unquoted PDF title metadata fails or changes valid filenames

**Location:** `src/idiomas/compile.py:129–130`.

The filename-derived title is inserted directly into a YAML metadata line. Punctuation accepted in filenames can instead be interpreted as YAML syntax.

**Reproduction:** pass `render_markdown(Deck(title))` to the installed Pandoc reader:

- `Food: fruit` returns exit code 64 with `mapping values are not allowed in this context`.
- `Food # drink` succeeds but its parsed title is only `Food`.

**Impact:** otherwise valid files cannot compile or display the wrong title. Inspect Tree's name prompts allow these titles.

**Suggested fix:** encode titles as properly escaped YAML strings, or pass title metadata through a mechanism that treats it as a literal value.

**Regression coverage:** real Pandoc metadata parsing for colons, hash signs, quotes, and bracket characters in titles.

### 6. [P2] Python string representations are not a safe TOML serializer

**Location:** `src/idiomas/config.py:90–104`.

Configuration values are written using Python's `repr()` via `!r`. Python and TOML do not have identical string literal rules.

**Reproduction:** save a config with user name `O'Brien "Nico"`, then call `load_config()`. The save succeeds but reload raises:

```text
TOMLDecodeError: Expected newline or end of document after a statement
(at line 1, column 17)
```

Confirmed using the actual `save_config`/`load_config` functions with a temporary config path. The same serialization method is used for root paths and language/input-method values.

**Impact:** the wizard can finish successfully yet write a configuration that prevents the next launch. Saving settings also uses this serializer.

**Suggested fix:** use a TOML serializer or a dedicated, correct TOML string encoder. Validate the serialized document before replacing the existing config.

**Regression coverage:** save/load strings containing both quote types, backslashes, and control characters.

### 7. [P2] Relative notebook roots depend on the launch directory

**Location:** `src/idiomas/tui/screens/wizard.py:448–456`; persistence/loading at `src/idiomas/config.py:85,93`.

The wizard validates a resolved path but retains only `Path(raw).expanduser()`. A relative input is saved as a relative path and is interpreted against each future process's working directory.

**Reproduction:** configure `notebooks` as the tree location from directory A, finish setup, then launch from directory B. The headless wizard probe confirmed it accepts and retains the relative root. A save/load reproduction from different working directories then failed during tree discovery with:

```text
FileNotFoundError: [Errno 2] No such file or directory: 'notebooks/tree-Chinese'
```

**Impact:** the same command fails or accesses a different notebook tree depending on where it is launched. CLI compilation may report everything up to date when the relative tree is absent because its file search returns no sources.

**Suggested fix:** resolve the selected root to an absolute path before storing it. Define an explicit recovery policy for existing relative-path configurations.

**Regression coverage:** finish setup with a relative root, change working directory, then reopen and compile the same notebook.

### 8. [P2] Creating a category named `Tags` produces an unusable category

**Location:** `src/idiomas/tui/screens/entry.py:461–471`; reserved-section handling at `src/idiomas/parser.py:43–48`.

Category creation accepts any nonempty name, including the reserved heading `Tags`. The writer emits `## Tags`, which the parser always treats as metadata rather than a category.

**Reproduction:** create a vocabulary category named `Tags`, then try adding an entry to the newly selected category. Confirmed in a headless Entry screen:

- The saved deck reloads with an empty category list.
- Adding the entry raises `StopIteration` when looking up the category.

If entry rows already exist beneath such a heading, the parser treats their fields as tags instead of entries. Grammar category creation also reparses the category immediately and encounters the missing category.

**Suggested fix:** reject the reserved category name before saving, or define an unambiguous representation that distinguishes categories from tag metadata.

**Regression coverage:** reserved-name creation through vocabulary and grammar forms, with a user-visible validation message and no file mutation.

### 9. [P2] A missing optional editor raises an unhandled exception

**Location:** `src/idiomas/tui/screens/inspect.py:393–397`.

The dependency checker explicitly treats Neovim as optional, but opening a Markdown file invokes `nvim` without handling its absence.

**Reproduction:** on a system without Neovim, select a file in Inspect Tree, switch to MD mode, and press Enter. A focused reproduction mocked the subprocess invocation to raise the missing-executable error and confirmed that `FileNotFoundError` escapes `_open_md`.

**Impact:** a supported installation without the optional editor cannot safely attempt this action; the event handler has no graceful error path.

**Suggested fix:** catch launch errors, restore the TUI, and notify the user that the editor is unavailable. Alternatively, disable the action with an explanatory message when the executable is missing.

**Regression coverage:** missing editor at action time; verify that the screen remains usable and the source file is untouched.

### 10. [P3] LaTeX escaping adds visible braces after literal backslashes

**Location:** `src/idiomas/compile.py:47–51`.

Escaping first substitutes a backslash with `\textbackslash{}`, then escapes the braces it just inserted. The result is `\textbackslash\{\}`, which prints extra braces.

**Reproduction:** compile an entry whose translation is `a\b`. A real Pandoc/XeLaTeX compilation followed by `pdftotext` extraction produced `a\{}b`.

**Impact:** literal backslashes in translations, notes, or other escaped fields render incorrectly in the PDF.

**Suggested fix:** escape the original input in one pass so replacement strings are not escaped again.

**Regression coverage:** literal backslash alone and next to braces, plus a real PDF output check.

## Additional findings (second pass)

### 11. [P2] Autocompile bypasses the staleness cache, so Compile can skip a stale PDF

**Location:** `src/idiomas/compile.py:218–247`; autocompile at `src/idiomas/tui/screens/base.py:54–73`.

`compile_all` skips a file when its PDF exists and the cached stamp matches the current source. Entry and Inspect Tree rebuild PDFs through `autocompile_one` → `compile_file`, which never updates that stamp. The cache can then describe an older source than the PDF on disk. If the source returns to that older state, Compile treats the newer PDF as up to date.

**Reproduction:**

1. Run Compile on a deck (the cache records stamp S1).
2. Add an entry in Entry and leave the screen. Autocompile rebuilds the PDF with the new entry.
3. Remove that entry outside the app, for example in another editor or with `git checkout`, so the source is back to S1.
4. Run Compile.

**Observed:** Compile reports nothing to rebuild, and `pdftotext` shows that the PDF still contains the removed entry. Confirmed with `compile_all` → `compile_file` → revert → `compile_all` against a temporary cache path.

**Impact:** the notebook can show entries that no longer exist in the source. Only Compile (force) or deleting the cache fixes it, and nothing tells the user it is needed.

**Suggested fix:** have every compile path record the stamp of what it just rendered, or store the stamp with the PDF so any writer keeps them in sync.

**Regression coverage:** compile_all → autocompile a changed source → revert the source → compile_all must rebuild.

### 12. [P2] A compile failure in Compile or Inspect Tree's open action terminates the TUI

**Location:** `src/idiomas/tui/screens/main_menu.py:61–67`; `src/idiomas/tui/screens/inspect.py:384–391`; cache save at `src/idiomas/compile.py:244–245`.

Only the autocompile worker catches compile errors. The main menu's Compile and Compile (force) call `compile_all` directly in the event handler. Inspect Tree's PDF-mode Enter calls `compile_file` directly when the PDF is missing. Neither catches `CalledProcessError`.

**Reproduction:** put a deck that fails to compile (finding 13's `C:\new words` heading, finding 5's `Food: fruit` title, or any XeLaTeX error) next to one that compiles. Then either:

- choose Compile in the notebook menu, or
- in Inspect Tree, press Enter on the failing file while it has no PDF.

**Observed:** both paths raise `CalledProcessError` out of the Textual app and end the session. Confirmed headlessly for both. In the Compile case, `compile_cache.json` was not written even though an earlier file had already been rebuilt during that run, because the cache is saved only after the loop finishes.

**Impact:** a single bad file makes the notebook menu's Compile unusable and takes the rest of the session down. Other files' rebuild work is lost from the cache, so the next run repeats it. From reading the code, the `idiomas compile` CLI prints a raw traceback for the same reason (`src/idiomas/__main__.py:37–48`).

**Suggested fix:** catch compile errors per file, report which files failed (with Pandoc's stderr), keep compiling the rest, and save the cache for the files that succeeded.

**Regression coverage:** one good and one failing file through menu Compile, Inspect open, and the CLI. Assert the app stays up, the failure is reported, and the good file's stamp is saved.

### 13. [P2] Category and subtitle names reach Pandoc as unescaped Markdown

**Location:** `src/idiomas/compile.py:137,143`.

Headings are emitted as `## {category.name}` and `### {subtitle.name}` with no escaping. Pandoc then reads heading attributes, closing `#` runs, emphasis, and raw TeX from them.

**Reproduction:** real Pandoc/XeLaTeX runs on category names:

| Category name | Result |
|---|---|
| `Food {#drinks}` | PDF heading is `Food`; `{#drinks}` becomes a label |
| `Level 2 #` | heading is `Level 2` |
| `*Very* common` | asterisks consumed as emphasis |
| `C:\new words` | `\new` passed through as raw TeX; compilation fails with `! Undefined control sequence.` |

**Impact:** valid category names, which Entry accepts without restriction, are printed incorrectly or stop the file from compiling. Combined with finding 12, the failing case also ends the TUI session.

**Suggested fix:** escape Markdown in heading text, or emit headings as raw LaTeX with the same `_escape` used for table cells.

**Regression coverage:** real Pandoc runs for attribute braces, trailing `#`, `*`/`_`, backslashes, and `$` in category and subtitle names.

### 14. [P2] Inspect Tree's name prompts accept path separators

**Location:** `src/idiomas/tui/screens/inspect.py:466–547` (rename, new directory, new file).

Names from `PromptDialog` are joined straight onto a parent path, so `/` and `..` are treated as path syntax. In a file rename, `_retitle` rewrites the file's header before `rename()` is attempted.

**Reproduction (headless, compile mocked):**

- Rename `food` to `sub/food2` when `sub/` does not exist: `FileNotFoundError` escapes the handler and ends the session. The file stays at `food.md` but its header is already `# sub/food2`.
- Rename `food` to `../outside`: the file moves out of the tree root to `outside.md` beside it, with header `# ../outside`. It no longer appears anywhere in the app.
- New file named `a/b` when `a/` does not exist: `FileNotFoundError` ends the session.

From reading the code, new directory (`n`) has the same pattern in `mkdir()`.

**Impact:** a mistyped name crashes the TUI, leaves a header that no longer matches its filename, or moves notebook files outside the tree where Compile, Browse, and Inspect Tree cannot see them.

**Suggested fix:** reject names containing path separators, `.`/`..`, or leading/trailing whitespace before touching the filesystem. Rewrite the header only after the rename has succeeded.

**Regression coverage:** `/`, `..`, and `../x` through rename (file and directory), new file, and new directory. Assert a user-visible error and no filesystem change.

### 15. [P2] A pasted tab character shifts entry fields

**Location:** form values at `src/idiomas/tui/screens/entry.py:369–377` and `406–409`; serialization at `src/idiomas/writer.py:10–11`.

Textual's `Input` drops newlines on paste but keeps tabs. Field values are written verbatim into the tab-separated row, so a tab inside a field becomes a column boundary.

**Reproduction:** in Entry, paste `苹果<TAB>apple` into Hanzi (for example a row copied from a spreadsheet or flashcard export), type `apple` as the translation, and press Create.

**Observed:** the saved row is `苹果\tapple\tping2guo3\tapple\tapple`, which reloads as hanzi `苹果`, pinyin `apple`, translation `ping2guo3`, and two extra fields. Confirmed headlessly. The hanzi value keeps the tab, and the auto-guessed pinyin becomes `ping2guo3\tapple`.

**Impact:** the entry is silently saved with the wrong pinyin and translation, and the PDF prints it that way. The same applies to Translation, Note, and the grammar form.

**Suggested fix:** strip or reject tab (and other control) characters in form fields before saving, and have the writer refuse to emit a field containing a tab.

**Regression coverage:** paste a tab into each form field, create, reload, and assert the fields are unchanged apart from the removed tab.

### 16. [P2] File contents and names are rendered as Textual markup

**Location:** MD-mode and text-fallback preview at `src/idiomas/tui/screens/inspect.py:277,314`; tree labels at `inspect.py:74` and `src/idiomas/tui/screens/entry.py:142–163`.

Preview text, file stems, and category names are passed as plain strings to `Static.update` and `Tree.add`, which parse them as markup.

**Reproduction (headless):**

- A deck containing `to [/] test` in a translation: switching Inspect Tree to MD mode on it raises `MarkupError: auto closing tag ('[/]') has nothing to close` and ends the session.
- A category named `Verbs [/x]`: opening Entry raises `MarkupError: closing tag '[/x]' ... doesn't match any open tag`. Entry cannot be opened while that file exists.
- `[b]…[/b]` or `[i]…[/i]` in content, filenames, or category names is silently stripped: a file named `[b]x` is listed as `x`, and `[@click=app.quit]x[/]` in a translation previews as `x`.

**Impact:** ordinary bracket text in a notebook can block Entry, crash Inspect Tree, or be shown differently from what is stored. The `pdftotext` fallback preview uses the same path.

**Suggested fix:** pass user text as literal `Content`/`Text`, or escape it with `textual.markup.escape`, everywhere it reaches a widget. Notification messages that interpolate hanzi or names deserve the same treatment.

**Regression coverage:** `[/]`, `[/x]`, and `[b]x[/b]` in file content, file names, category names, and subtitle names through Entry, Inspect Tree (both modes), and SelectField labels.

### 17. [P3] A case-only rename is refused on macOS

**Location:** `src/idiomas/tui/screens/inspect.py:471,479`.

The collision check uses `exists()`, which is true for the file itself on a case-insensitive filesystem such as default APFS.

**Reproduction:** in Inspect Tree, rename `food` to `Food`. Confirmed headlessly on macOS: the rename is rejected as already existing, and the file stays `food.md` with header `# food`. Directory renames use the same check.

**Suggested fix:** treat the target as free when it resolves to the same file (`samefile`), and rename through a temporary name if the platform requires it.

**Regression coverage:** case-only rename of a file and of a directory.

### 18. [P3] Creating a category that already exists yields an unusable duplicate

**Location:** `src/idiomas/tui/screens/entry.py:461–471`; lookup at `entry.py:382,401`.

Category creation never checks for an existing name, although subtitle creation does (`entry.py:416`). Every lookup takes the first category with a matching name.

**Reproduction:** in a deck that already has `Food`, create a category named `Food`, then add an entry to the newly selected category. Confirmed headlessly: the file gets a second `## Food` heading, the entry lands under the first one, and the second stays empty. Both tree leaves target the first heading.

**Suggested fix:** reject a duplicate name with a message, or select the existing category as subtitle creation does.

**Regression coverage:** duplicate category creation in vocabulary and grammar files.

### 19. [P3] Pinyin is misattributed next to Latin letters and digits

**Location:** `src/idiomas/pinyin.py:30,50`; grammar pairing at `src/idiomas/compile.py:59–68`.

`guess()` keeps non-hanzi characters in its output without separators. The syllable regex then glues adjacent Latin letters onto the next syllable and drops letters that have no tone digit.

**Reproduction:**

| Hanzi | `guess()` | Vocabulary PDF | Grammar pairing |
|---|---|---|---|
| `T恤` | `Txu4` | `Txù` | `Txù` under 恤 |
| `3D打印` | `3Dda3yin4` | `Ddǎyìn` | `Ddǎ` under 打 |
| `X光` | `Xguang1` | `Xguāng` | `Xguāng` under 光 |
| `卡拉OK` | `ka3la1OK` | `kǎlā` (`OK` dropped) | correct |

**Impact:** common loanword entries print incorrect pinyin, and Entry's pinyin field is read-only, so the user cannot correct it.

**Suggested fix:** keep non-hanzi segments separate in the guessed pinyin (or leave them out), and match syllables only on lowercase pinyin letters.

**Regression coverage:** guess → vocabulary rendering → grammar pairing for mixed Latin/digit/hanzi words.

## Recommended order

1. Fix pending-delete path tracking and preserve empty tab-separated fields (findings 1–2).
2. Fix parser/writer and configuration round trips, including reserved category names and pasted tabs (3, 6, 8, 15).
3. Stop crashes on ordinary input: compile error handling, name validation, and markup escaping (12, 14, 16).
4. Fix compile output correctness: the staleness cache, heading escaping, pinyin rendering, and title encoding (11, 13, 4, 5).
5. Fix relative roots and missing-editor handling (7, 9).
6. Correct the low-priority rendering and naming issues (10, 17, 18, 19).

All fixes above are recommendations; none have been applied.
