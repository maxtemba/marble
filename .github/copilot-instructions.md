# Guidance for AI coding agents — nas-project-marble

This project is a very small NAS (neural architecture search) toy workspace. The goal of these instructions is to make an AI coding agent immediately productive by describing the project's structure, conventions, and concrete examples.

Primary files
- `search_space.py` — defines the search-space primitives:
  - `OPS`: allowed operation names (e.g. `'3x3_conv'`, `'relu'`).
  - `NetworkBlock(op_type, params)` — the atomic element with `.op_type` and `.params`.
  - `Architecture(blocks)` — container holding `blocks` (list of `NetworkBlock`).
  - `get_random_architecture(max_depth=5)` — helper to generate random Architectures.

- `predictor.py` — simple latency predictor demo pipeline:
  - `featurize(arch: Architecture)` converts an `Architecture` into a numeric vector: `[total_depth, total_convs, max_filter]`.
  - Generates dummy training data using `get_random_architecture()` and a simple synthetic latency formula.
  - Trains a `sklearn.ensemble.RandomForestRegressor` and prints a sample prediction.

Big-picture and intent
- This repo is a toy demonstrator for NAS components: a minimal search-space (`search_space.py`) and a predictor prototype (`predictor.py`). Expect code to be small, self-contained, and focused on examples rather than production features.
- The predictor uses synthetic labels (dummy latency). Real workflows will replace the dummy data generation with measured latencies or dataset-driven targets.

Conventions and patterns (explicit)
- Data objects are thin classes with public attributes (no dataclasses/typing used). Use `.blocks`, `.op_type`, and `.params` to inspect objects.
- Random helpers live in `search_space.py` — prefer using `get_random_architecture()` when tests/examples need architectures.
- Feature extraction lives in the predictor (`featurize`) and is intentionally simple. When adding features, follow the same deterministic, small-vector approach (avoid side-effects).

What an agent should do first (concrete checklist)
1. Read `search_space.py` to understand `NetworkBlock` and `Architecture` shapes.
2. Read `predictor.py` to see how features are extracted and how the dummy pipeline is wired.
3. When adding a new feature, add unit tests that construct `Architecture` via `get_random_architecture()` and assert `featurize(...)` output shape and ranges.
4. If replacing dummy labels with real measurements, add a small adapter that accepts a CSV of (arch, latency) pairs and transforms arch -> features using `featurize`.

Examples to reference in code changes
- Feature vector: `predictor.featurize` returns numpy array `[total_depth, total_convs, max_filter]` — keep this format stable unless you update callers.
- Random architecture creation: `search_space.get_random_architecture(max_depth=5)` — use for reproducible examples.

Build / run / test notes
- No project-level build system detected. Files are runnable as simple Python scripts.
- Minimal dependency: scikit-learn and numpy. If running locally, create a venv and install required packages before executing `predictor.py`.

Edge cases and constraints discovered from code
- `NetworkBlock.params` assumed to contain `'filter'` in predictor; guard code changes against missing keys.
- `featurize` checks for `'conv'` substring in `op_type` to count convolutions — new op names should follow this naming pattern or `featurize` must be updated.

Touch points for future work (low-risk)
- Add `requirements.txt` with `numpy` and `scikit-learn` for reproducible runs.
- Add small unit tests for `featurize` and `get_random_architecture`.
- Replace synthetic latency generator with a CSV loader adapter.

If you change APIs
- Update `predictor.featurize`'s documented output shape here. Callers (and tests) expect a 3-element numpy array.

If `.github/copilot-instructions.md` already existed, note
- No prior instructions were present in the repository root under `.github/`.

If anything in these instructions is unclear or you'd like deeper coverage (tests, requirements, or a demo runner), tell me which part to expand and I'll iterate.