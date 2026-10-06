# M6 · Publishing — requirements

## Anchor: the roadmap

From [`../../roadmap-sprint-7.md`](../../roadmap-sprint-7.md), *M6 · Publishing*:

> **Deliverable.** A public GitHub repo whose single commit is the current tracked
> tree, minus whatever else the spec rules out, and that passes a leak check. The
> local clone is then working against it as `origin`, and feature work after
> this point opens its PRs there.
>
> **Done when.** The public repo exists with one commit, the leak check over it
> is clean, no backlog is in it, a fresh clone of it installs by M5's README,
> and the local clone pushes to it. The dev then deletes the private repo
> themselves.

The backlog, *Publishing*: "Create a new repo with what's current, preventing
leaks. The only exception of what's current is the individual sprints backlogs,
these should not be published (as per the skill)".

Added by the dev when M6 started (2026-10-05): **the app is renamed from
Idiomas to Vimdiomas**, "everywhere in the code before uploading". The public
repo is <https://github.com/Nicostalman/Vimdiomas>, which the dev had already
created as public, with GitHub's *Initial commit* holding a GPL-3.0 `LICENSE`
and the description "Guardar vocabulario rápidamente en una TUI con Vim
keybindings. Nada de Anki!".

## Decisions

Settled with the dev in the spec conversation, 2026-10-05.

| Decision | Rationale |
| --- | --- |
| **Full rename, with migration of the old paths** | Dev's choice from three (full with migration, full without, user-facing only). The package, the command, the config and cache folders, the app class and every user-facing string become Vimdiomas. An existing install keeps working (§2). |
| **The published tree is the current tracked tree, minus the backlogs** | Dev's choice: `specs/`, `.claude/skills/`, `CLAUDE.md` and the sprint artifacts (`comparison.pdf/.tex`, `check_equivalence.py`) are all published. The SDD process is part of the project. |
| **The code lands as one commit on top of GitHub's *Initial commit***, not a force-pushed single root | Dev's choice. The `LICENSE` commit is kept, so the public history has two commits and nothing is force-pushed. This supersedes the roadmap's "single commit". The `LICENSE` file is also added on the branch, so that the private `main`'s tree and the published tree are identical. |
| **The old history is kept in a git bundle outside the repo** | Dev's choice (after a bundle was explained: one file holding a repo's history, cloneable, not pushable by accident). `~/Ego/Computing/idiomas-history.bundle`. It sits outside the working tree, so no `.gitignore` entry is needed. Local `main` then follows the public repo only. |
| **Commits to the public repo use the GitHub noreply email** | Dev's choice. `270777602+Nicostalman@users.noreply.github.com`, set as this clone's local `user.email`. The dev's global email is untouched. The *Initial commit* GitHub made already shows the dev's gmail, and it stays as it is. |
| **The `/Users/<name>` path in a frozen Sprint 4 plan is redacted** | Dev's choice, an **explicit exception to the frozen-sprint rule**, recorded in `notes-sprint-7.md`. It is the only leak the scan found: `specs/Sprint-4/features/M4-2026-09-13-install-groundwork/plan.md` line 173 becomes `/Users/you/...`, the placeholder the code already uses. |
| **The leak check is a script kept in the repo**: `scripts/leak_check.sh` | Dev's choice. It hardcodes nothing personal: it reads the patterns from `git config --global user.email`, `$HOME` and `whoami` at run time, so publishing it leaks nothing. |
| **Closed sprints keep the name Idiomas** | Sprints 1–6 are frozen, and their specs are records of their time. The Sprint 4 redaction above is the only edit there. Sprint 7's roadmap and its M1–M5 specs describe merged work and keep the old name too. `specs/current/` and Sprint 7's notes describe the project now, and are renamed. The changelog's past sections are records and are not renamed. |
| **The local folder `~/Ego/Computing/Idiomas` is not renamed by the agent** | Moving it would break the venv, the `~/.local/bin` link and this session. It's the dev's call, after the merge. Nothing in the repo depends on the folder's name. |

## 1. The rename

Every tracked file outside the exceptions above: `src/`, `tests/`,
`pyproject.toml`, `uv.lock`, `docker/`, `readme.md`, `CLAUDE.md`,
`.claude/skills/`, `specs/current/` (except past changelog sections) and
`specs/Sprint-7/guidelines/notes-sprint-7.md` (entries written from M6 on).

| Was | Becomes |
| --- | --- |
| `src/idiomas/`, `import idiomas` | `src/vimdiomas/`, `import vimdiomas` |
| `pyproject.toml` name, script, package-data key | `vimdiomas` |
| The command `idiomas` (and `idiomas doctor`, `idiomas compile`) | `vimdiomas` |
| `~/.config/idiomas/config.toml` | `~/.config/vimdiomas/config.toml` |
| `~/.cache/idiomas/compile_cache.json` | `~/.cache/vimdiomas/compile_cache.json` |
| `~/.local/bin/idiomas` link | `~/.local/bin/vimdiomas` |
| Wizard default root `~/Documents/Idiomas` | `~/Documents/Vimdiomas`, for new installs only |
| `IdiomasApp`, "Idiomas" in prompts and messages | `VimdiomasApp`, "Vimdiomas" |
| README title and clone URL `Nicostalman/Idiomas.git`, `~/.local/share/idiomas` | `Vimdiomas`, `Nicostalman/Vimdiomas.git`, `~/.local/share/vimdiomas` |
| Docker image tag `idiomas-linux`, container paths | `vimdiomas-linux`, `vimdiomas` |

A notebook's root stays where the config says. The dev's `root =
'/Users/…/Documents/Idiomas'` is not moved or renamed.

## 2. Migration of an existing install

`vimdiomas.config.migrate_legacy_paths()`, run by `__main__` before the config is
loaded, on every start. Each step only acts when its condition holds, so it is a
no-op after the first run and on a fresh machine:

1. `~/.config/idiomas/` exists and `~/.config/vimdiomas/` does not: the folder
   is moved (`os.replace`), backups such as `config.toml.bak` included.
2. `~/.cache/idiomas/` exists and `~/.cache/vimdiomas/` does not: moved the
   same way, so the first Compile after the rename is not a full rebuild.
3. `~/.local/bin/idiomas` is a symlink whose target's name is `idiomas` (the
   only kind the installer ever made) **and the target no longer exists**:
   the dangling link is removed. A working link, or anything that isn't a
   symlink, is left alone.

Never raises: an `OSError` in any step is swallowed, and the app starts as it
would without migration (a failed step 1 means the wizard runs). Nothing is
printed. The `$PATH` line the installer added to the shell config needs no
migration: it names `~/.local/bin`, not the command, and its dedupe check
matches the folder.

After the merge, the dev runs `uv sync` (or the README's install) in their clone
so that `.venv/bin/vimdiomas` exists, then starts it once by full path, which
runs the migration and, through the wizard's existing link step on the next
setup, or by hand, makes `~/.local/bin/vimdiomas`. Exact steps are in
`validation.md` §4.

## 3. Untracking the backlogs (moved from M1)

- `git rm --cached` Sprint 2's `guidelines/motivation.md` and Sprint 3–6's
  `guidelines/backlog.md`. The files stay on disk.
- `.gitignore` gets `specs/Sprint-2/guidelines/motivation.md`.
- M1's `validation.md` §1 checks are run (see this milestone's `validation.md`
  §2).

## 4. The leak check

`scripts/leak_check.sh [ref [base]]`, defaults `HEAD` and `origin/main`, run from the repo root. It scans
the **tree at `ref`** (`git grep` on the ref, so untracked and ignored files are
never involved) and fails (exit 1, listing every hit) on:

- the global git email (`git config --global user.email`), if set;
- `$HOME` and `/Users/$(whoami)` / `/home/$(whoami)`;
- token shapes: `ghp_`, `gho_`, `github_pat_`, `sk-…` (20+ chars),
  `-----BEGIN … PRIVATE KEY-----`;
- any tracked path named `backlog.md`, `motivation.md` under `guidelines/`, or
  `postponedfeatures.md`, or starting `bug-report-`... at the repo root.

It also checks the **author and committer emails** of every commit in
`ref` that `base` doesn't have, and fails on the global email. `base` is an
argument because at publish time the commit sits on `public/main`, not on the
private `origin/main` (found at implementation). It prints `leak check: clean` and exits 0 otherwise. The script excludes
itself from the content scan. It needs only `git`, `grep` and POSIX `sh`.

## 5. The publish and the switch

In this order, so that the old history always exists somewhere:

1. The branch is squash-merged into the private `origin` as usual (PR there),
   and the settled notes are committed on `main` after it.
2. `git bundle create ~/Ego/Computing/idiomas-history.bundle --all` and
   `git bundle verify` it.
3. The public repo is added as remote `public`, fetched. A commit is made with
   `git commit-tree main^{tree} -p public/main`, author and committer the
   noreply email, message *Vimdiomas* with a short body. Its diff against
   `public/main` only adds files (`LICENSE` is identical).
4. `scripts/leak_check.sh <that commit> public/main` passes. Then it is pushed to
   `public/main` as a fast-forward. No `--force`.
5. `origin` is re-pointed to `https://github.com/Nicostalman/Vimdiomas.git`,
   `public` is removed, and local `main` is reset to `origin/main`. Local
   branches other than `main` are none.
6. `git config user.email` (local) is set to the noreply email.
7. A fresh clone of the public repo installs by the README (validation §5).
8. The dev deletes the private repo `Nicostalman/Idiomas` themselves. The agent
   does not.

Sprint 7's close (the `changelog` skill) runs after this, on the new `main`,
and is the first commit pushed through the re-pointed `origin`.

## Out of scope

- Renaming the dev's notebook root or the local clone folder.
- Moving `postponedfeatures.md` or the bug report (both already ignored).
- Changing the repo's description or license.
- Brew or PyPI packaging.
