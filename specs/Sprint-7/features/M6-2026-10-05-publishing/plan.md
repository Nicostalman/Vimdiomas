# M6 · Publishing — plan

The task groups are ordered so that each one depends only on the groups before
it. Section numbers (§) refer to [`requirements.md`](requirements.md).

## 1. Rename (§1)

- `git mv src/idiomas src/vimdiomas`.
- Replace `Idiomas`→`Vimdiomas`, `idiomas`→`vimdiomas` in the files §1 lists,
  one pass each, skipping frozen sprints, Sprint 7's roadmap and M1–M5 specs,
  and past changelog sections.
- `IdiomasApp` → `VimdiomasApp`.
- `uv lock` so `uv.lock` names `vimdiomas`.
- Review the diff for anything the substitution got wrong (prose that meant
  "languages", historical references in docstrings that name a sprint).

## 2. Migration (§2)

- `migrate_legacy_paths()` in `config.py`, called first in `__main__`.
- Tests in `tests/test_config.py` with a temporary `HOME`: each of the three
  steps, the no-op cases, a working link left alone, and an `OSError` swallowed.

## 3. Backlogs and redaction (§3, the frozen-sprint exception)

- `git rm --cached` the five files; `.gitignore` line for `motivation.md`.
- Redact line 173 of Sprint 4 M4's `plan.md`.

## 4. Leak check and license (§4, §5)

- `scripts/leak_check.sh`, executable.
- `LICENSE` copied byte for byte from `public/main`.
- `stack.md`: a line on the leak check and the license.

## 5. Checks before the PR

- Full test suite.
- `scripts/leak_check.sh` on the branch.
- validation.md §1–§3.

## 6. Hand-off, merge, publish (§5)

- Stop for the dev's review.
- PR on the private origin, squash-merge, cleanup per `feature-spec` step 9.
- Notes on `main`.
- The publish and switch, §5 steps 2–7, then validation.md §5–§6.
