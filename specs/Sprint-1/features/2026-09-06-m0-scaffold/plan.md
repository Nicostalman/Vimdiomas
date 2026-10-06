# M0 · Documentation and scaffold — Plan

## 1. Packaging metadata

1.1. Write `pyproject.toml`: `[build-system]` (setuptools), `[project]` with `name = "idiomas"`, Python `>=3.14` requirement, and a `src` layout declaration (`[tool.setuptools.packages.find] where = ["src"]`).

1.2. Add `[project.optional-dependencies] dev = ["pytest>=8"]`, matching `stack.md`.

## 2. Package skeleton

2.1. Create `src/idiomas/__init__.py` (empty, marks the package).

2.2. Create `src/idiomas/__main__.py` with a `main()` that does nothing but return, and a `if __name__ == "__main__": main()` guard, so `python -m idiomas` starts and exits cleanly with status 0.

## 3. Repo hygiene

3.1. Write `.gitignore`: `.venv/`, `__pycache__/`, `*.pyc`, `.pytest_cache/`, `*.egg-info/`, `build/`, `dist/`.

3.2. Create the empty `source/` and `notebook/` trees (each needs a `.gitkeep` or similar, since git doesn't track empty directories).

## 4. Environment and verification

4.1. Create the venv (`python3 -m venv .venv`) and activate it.

4.2. Run `pip install -e ".[dev]"` and confirm it succeeds with no errors.

4.3. Run `python -m idiomas` and confirm it starts and exits with status 0.

4.4. Run `pytest` (even with zero tests collected) to confirm the dev environment is wired up correctly for M1 onward.
