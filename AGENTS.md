# Repository Instructions

## Project Shape

- This repo builds Presence Timeline, a private self-hosted Home Assistant location history service.
- `backend/` contains the FastAPI service, SQLAlchemy/PostGIS models, Alembic migrations, workers, providers, and pytest suite.
- `custom_components/presence_timeline/` contains the Home Assistant custom integration and frontend panel assets intended for HACS-style delivery.
- `docs/` contains architecture and roadmap notes.
- `docker-compose.yml` runs the local API, PostGIS database, migrator, and background workers.

## Shell And Tooling

- Prefix shell commands with `rtk` unless a command is known to require `rtk proxy`.
- Prefer `rg` and `rg --files` for searching.
- Use `apply_patch` for manual file edits.
- Do not use destructive git commands such as `git reset --hard` or `git checkout --` unless explicitly requested.
- Do not revert user changes. If unrelated files are dirty, leave them alone.

## Backend Build And Verification

- Backend runtime targets Python 3.13.
- From `backend/`, install development dependencies with:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
```

- Run backend tests from `backend/` with:

```bash
pytest
```

- Run focused backend tests with:

```bash
pytest tests/<test_file>.py
```

- Run Ruff checks from `backend/` when Python code style or imports change:

```bash
ruff check .
```

- Schema changes must go through Alembic migrations under `backend/alembic/versions/`.
- Apply migrations from `backend/` with:

```bash
alembic upgrade head
```

## Home Assistant Integration And Frontend Verification

- Integration code lives under `custom_components/presence_timeline/`.
- Frontend utility tests use Node's built-in test runner. Run focused tests with:

```bash
node --test custom_components/presence_timeline/frontend/*.test.mjs
```

- Keep HACS-facing metadata in `hacs.json` and `custom_components/presence_timeline/manifest.json` aligned when packaging behavior changes.

## Local Runtime

- Start the local stack with:

```bash
docker compose up --build
```

- Use `docker compose config` after editing Compose files.
- Long-running services should use `restart: unless-stopped`; one-shot jobs such as the Alembic migrator should not.

## Workflow Policy

- Classify each task as micro, lightweight, or full before implementation.
- Use strict TDD for behavioral, risky, regression-prone, API, auth, validation, data, migration, or bug-fix changes.
- Documentation-only, copy, sample config, formatting, and obvious non-runtime cleanup can be implementation-first with explicit verification.
- Verify before claiming completion. Use the smallest command or review that proves the claim, then report the exact verification result.
- Commit after every completed workflow. Stage only files that belong to the workflow, and do not sweep in unrelated dirty changes.
- Push after verified completion. Also push earlier when remote CI, deployment, or integration testing needs the branch state.
- If verification cannot be run, state why, describe the residual risk, then commit the completed work if it is still coherent.
