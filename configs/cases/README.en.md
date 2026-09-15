# Case configuration (CaseSpec)

**[中文版（Chinese）](README.md)**

A CaseSpec describes every protocol fact of one case: the case text, the prompt variants, the
`trial_id` prefix, the extraction vocabulary and the version pins. Bringing your own case means
filling in one `<case_id>.json` in this directory — no code changes.

- Loader and validation: `src/medmirror/casespec.py` (`load_case_spec`)
- Origin: issue #50 (plan/003 step 2.2, first half); the default case `carotid_plaque_001.json`
  is proven by `tests/test_casespec_replay.py` to be free of semantic drift from the 27 historical
  exp003 requests.

## Fields

| Field | Type | Constraint | Notes |
|---|---|---|---|
| `case_id` | str | non-empty | Unique case identifier; the file name must be `<case_id>.json` |
| `protocol_version` | str | non-empty | Protocol version pin (written into the plan and the materialized view, for audit) |
| `trial_prefix` | str | `^[a-z0-9][a-z0-9_-]*$` | `trial_id` prefix (`<prefix>-<model>-<variant>-<index>`) |
| `case_text` | str | non-empty | The case statement text (the body of the baseline prompt) |
| `synthetic` | bool | must be `true` | Synthetic-case declaration (explicit boolean: real patient data does not enter the experiment, an intent.md red line; no valid falsy value is expressible) |
| `variants` | {name: str} | non-empty object, names and prompts non-empty | Prompt variants: variant name → full prompt text |
| `extraction.extractor_version` | str | must equal the extractor version the code supports | The vocabulary is bound to extractor semantics; a mismatch refuses to load |
| `extraction.paths` | {path: [term]} | non-empty object, term lists non-empty with non-empty terms | Path vocabulary: path name → trigger terms |
| `notes` | str | non-empty | Case description (editorial notes such as provenance and boundaries) |

The schema is closed: unknown top-level keys and unknown keys inside `extraction` are always
rejected; duplicate JSON keys are rejected (so a later key cannot silently overwrite an earlier
one); variant names and path names reject control characters and `|` (which would corrupt the
`trial_id` and the report structure). Adding a field is a schema change and requires explicit
review — nothing is swallowed silently.

## Vocabulary registry (vocab-registry.json)

`configs/cases/vocab-registry.json` registers `case_id|protocol_version|extractor_version →
vocabulary digest (sha256)`. For a CaseSpec **directly under the cases directory** (not in a
subdirectory), loading enforces:

- unregistered version triple → refused (a new case or a version bump must append a registration
  line explicitly, through review);
- registered triple but a different vocabulary digest → refused (changing the vocabulary under the
  same version violates the "changing the vocabulary = a new version number" red line).

The correct way to change a vocabulary: raise `protocol_version` or switch `extractor_version`,
then add a line to the registry file. Third-party custom paths outside this directory are not
subject to the registry (self-discipline applies); a CaseSpec placed in a subdirectory takes the
same route — the guard checks the direct parent directory, which is a known implementation
boundary.

## Protocol red lines

- **Changing the vocabulary or variants of an existing case = a new extractor/protocol version
  number**, and historical artifacts are never rewritten (the measuring-stick discipline of
  `.42cog/` and `specs/calibration.md`). **What is gated mechanically**: the registry digests the
  **vocabulary** only. Variant changes are **not** covered by the registry gate today — they are
  held by discipline and by review (a logged gap).
- When the `extractor_version` pinned by a CaseSpec does not match the version supported by
  `src/medmirror/protocol.py`, loading is **refused** (the error carries both version values); the
  version string has a single source in `protocol.EXTRACTOR_VERSION`.
- The synthetic-case declaration must be truthful: real patient data does not enter the experiment
  (an intent.md red line).

## How to onboard a new case (current boundary)

1. Copy `carotid_plaque_001.json` to `<case_id>.json` and rewrite it field by field;
2. smoke-check it (loading performs full validation):

   ```bash
   uv run python -c "
   from pathlib import Path
   from medmirror.casespec import load_case_spec
   from medmirror.protocol import EXTRACTOR_VERSION
   spec = load_case_spec(Path('configs/cases/<case_id>.json'),
                         supported_extractor_version=EXTRACTOR_VERSION)
   print(spec.case_id, spec.trial_prefix, list(spec.variants), list(spec.paths))
   "
   ```

3. use it at library level (case and vocabulary are threaded through the whole chain):

   ```python
   from medmirror.casespec import load_case_spec
   from medmirror.protocol import EXTRACTOR_VERSION
   from medmirror.runner import planned_trials

   spec = load_case_spec(path, supported_extractor_version=EXTRACTOR_VERSION)
   plan = planned_trials(registry, repeats=3, spec=spec)  # plan (messages/trial_id/endpoint)
   # execute: runner.execute_run(..., spec=spec) (budget gate and resume semantics unchanged)
   # extract: protocol.extract_trial(trial, paths=spec.extraction_paths)
   # report:  reporting.extract_sorted(trials, paths=...) / build_report(..., paths=...)
   #          / render_markdown(report, paths=...) — extraction and reporting must share one vocabulary
   ```

**Boundary (as of issue #50)**: there is no `--case` execution CLI yet — `scripts/run_exp003_baseline.py`
is anchored to the default exp003 case; running a baseline for a new case is plan/003 step 2.3
(which requires the case to be approved and a new protocol version), so the onboarding surface today
is configuration plus the library-level API. When a vocabulary falls outside the expressive range of
the v2 vocabulary, step 2.4 routes it into `needs_review`.
`render_markdown` is the exp003-branded renderer (its title and pointer text are anchored to
exp003); cross-case rendering awaits a new report version, so for other cases use the structured
JSON artifact as the report form (see `docs/experiments/exp003-baseline/derived-v3/analysis.json`).
This project runs from a repository clone plus `uv sync` (no pip package is published): the default
case is read from the repository-relative `configs/cases/` at import time of `medmirror.protocol` /
`medmirror.runner`, and the wheel layout does not include that directory (packaging it is deferred
until distribution is needed). A custom CaseSpec loaded through `load_case_spec(<any path>)` does
not depend on the directory inside the repository.
