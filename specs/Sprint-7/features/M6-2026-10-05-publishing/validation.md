# M6 · Publishing — validation

The acceptance bar. Section numbers (§) refer to
[`requirements.md`](requirements.md).

## 1. Rename (§1)

- [x] `git grep -l -iP "(?<!vim)idiomas" -- src tests pyproject.toml uv.lock docker readme.md CLAUDE.md .claude specs/current/{mission,stack,design,README}.md`
      lists only `src/vimdiomas/config.py`, `tests/test_config.py` (the
      legacy names the migration needs) and `specs/current/stack.md` ("was
      called Idiomas").
- [x] `uv run vimdiomas --help` works. `uv run python -m vimdiomas --help` works.
- [x] `uv.lock` names `vimdiomas`.
- [x] Full test suite passes (1462 tests).

## 2. Backlogs (§3)

- [x] `git ls-files | grep -E 'guidelines/(backlog|motivation)\.md'` prints
      nothing.
- [x] The five files are still on disk.
- [x] `git check-ignore` matches each of them.

## 3. Leak check (§4)

- [x] `scripts/leak_check.sh` prints `leak check: clean` on the branch.
- [x] Planting the global email in a scratch commit makes it fail with that
      file listed (then the commit is dropped).
- [x] `grep -n "/Users/$(whoami)" specs/Sprint-4/features/M4-2026-09-13-install-groundwork/plan.md`
      prints nothing.

## 4. Migration, on the dev's machine (§2)

In the clone: `uv sync --extra dev`, then run `.venv/bin/vimdiomas` once.

This ran on the dev's machine during implementation: the agent's
`uv run vimdiomas --help` went through `main()` and migrated for real
(2026-10-06). The file checks below were confirmed then, and the agent made the
`~/.local/bin/vimdiomas` link. The two app checks are the dev's.

- [ ] It opens on the landing menu with the dev's notebooks, no wizard.
- [x] `~/.config/vimdiomas/config.toml` exists (with both `.bak` files), and
      `~/.config/idiomas/` does not.
- [x] `~/.cache/vimdiomas/compile_cache.json` exists.
- [ ] A Compile right after rebuilds nothing.
- [x] `~/.local/bin/idiomas` is gone (it dangled once `uv sync` removed
      `.venv/bin/idiomas`). `~/.local/bin/vimdiomas` links to
      `.venv/bin/vimdiomas`.
- [ ] `vimdiomas` works from a new shell.

## 5. The public repo (§5)

- [ ] `git bundle verify ~/Ego/Computing/idiomas-history.bundle` succeeds and
      `git bundle list-heads` shows the old `main`.
- [ ] `gh api repos/Nicostalman/Vimdiomas/commits` lists exactly two commits:
      *Initial commit* and *Vimdiomas*, the latter authored by the noreply
      email.
- [ ] `scripts/leak_check.sh origin/main` is clean.
- [ ] No `backlog.md` or `motivation.md` in `git ls-tree -r origin/main`.
- [ ] A fresh `git clone https://github.com/Nicostalman/Vimdiomas.git` into a
      scratch folder, then the README's install commands, gives a
      `.venv/bin/vimdiomas` whose `doctor` runs.

## 6. The switch

- [ ] `git remote -v` shows only `origin` → `Nicostalman/Vimdiomas`.
- [ ] `git status` on `main` is up to date with `origin/main`, and
      `git branch` lists `main` only.
- [ ] `git config user.email` is the noreply email.
- [ ] The dev deletes `Nicostalman/Idiomas` (their action).
