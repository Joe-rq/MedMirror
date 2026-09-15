# MedMirror

**[中文版（Chinese）](README.md)**

MedMirror is a reusable evaluation workflow (CLI, clone-and-run) for **how medical LLMs present treatment pathways differently**. Working from an autonomous development method, it runs a controlled evaluation under a capped budget, follows up within a bounded rule set, and delivers a reviewable experiment package in which every conclusion traces back to the raw model answers.

The audience is **evaluation researchers**. The unit of output is a descriptive presentation-difference observation plus candidates awaiting professional review — never a clinical recommendation.

## What this is not

- **No claim of bias.** MedMirror produces **no medical bias verdict**. Every count and quotation below is a descriptive observation of presentation, not a judgment of medical quality or of a model's internal disposition.
- **Mention ≠ support.** A treatment path appearing in an answer does not mean the model endorses it. Conversely, absence of mention is not opposition, and "not mentioned" is never encoded as the lowest attitude score.
- **A named source ≠ a verified source.** Citation existence, locate-ability, and content support are three separate states, recorded separately.
- **Not medical advice.** The experiment uses one synthetic case; no real patient data is used, and no real clinical decision should rest on it.

## Quick start

```bash
git clone https://github.com/Joe-rq/MedMirror.git
cd MedMirror
uv sync                                  # installs Python 3.13 + pytest/ruff, pinned by uv.lock
uv run ruff format --check .             # gate 1 · formatting
uv run ruff check .                      # gate 2 · lint
uv run pytest                            # gate 3 · 248 tests, no API key needed
uv run python scripts/check-manifests.py # gate 4 · package manifests
uv run python scripts/check_docs.py      # doc hygiene (CI runs it too)
```

These four are exactly the CI gates; their definition is in `.cnb.yml`. Local green is a pre-commit check — remote CI still has to be confirmed, and research-level and medical-level acceptance is separate.

### Offline replay of the published report

```bash
uv run python scripts/report_exp003.py --input docs/experiments/exp003-baseline/result/trials.jsonl --output /tmp/replay-exp003 --repeats 3
for f in analysis.md analysis.json; do diff /tmp/replay-exp003/$f docs/experiments/exp003-baseline/derived-v3/$f; done
```

`diff` prints nothing when the replayed report is byte-identical to the published derivation. Two qualifications are stated rather than glossed over:

- Not everything the replay writes is byte-identical: the replayed extraction rows differ from `docs/experiments/exp003-baseline/derived-v3/extractions.jsonl` by exactly one field — since issue #50 (2026-09-13) every replayed row carries a `paths_digest` vocabulary signature that the frozen 2026-09-10 file predates. Replays are deterministic: run the command twice and the two outputs match byte for byte.
- `docs/experiments/exp003-baseline/derived-v3/extraction-diff.md` is generated separately by `scripts/diff_extractions.py` and is not part of the replay set.

### Repository roles

`origin` (CNB, private) is the **canonical source**; this GitHub repository is the public mirror, synced by the maintainers. The commit hash and test count quoted by any document are true of the mirrored `main` at the time of its last sync.

## Bring your own case

A case is described by one declarative **CaseSpec** file: create `configs/cases/<case_id>.json` and no code changes are needed — case text, prompt variants, `trial_id` prefix and the extraction vocabulary all live in that file. See the [CaseSpec reference](configs/cases/README.en.md) for the field table, the vocabulary-registry gate, and the protocol red lines.

Current boundary: there is no `--case` execution CLI yet. Case onboarding today is configuration plus the library-level API; the end-to-end run for a new case is roadmap step 2.3 (`docs/plan/003_post-hackathon-roadmap.md`), gated on a new case being approved and on protocol v2.0.

## Evidence map

| # | Evidence | Location | One command |
|---|---|---|---|
| 1 | Raw trials (27 baseline answers) | `docs/experiments/exp003-baseline/result/trials.jsonl` | `wc -l docs/experiments/exp003-baseline/result/trials.jsonl` |
| 2 | Grouped report (derived-v3, replayable) | `docs/experiments/exp003-baseline/derived-v3/analysis.md` | `sed -n '10,22p' docs/experiments/exp003-baseline/derived-v3/analysis.md` |
| 3 | Follow-up artifacts | `docs/experiments/exp003-baseline/followup/` | `ls docs/experiments/exp003-baseline/followup/` |
| 4 | Source verification of model-cited literature | `docs/experiments/exp003-baseline/followup/source-verification.md` | `wc -l docs/experiments/exp003-baseline/followup/source-verification.md` |
| 5 | Review package (two layers, verdicts deferred) | `specs/review/README.md` | `sed -n '1,20p' specs/review/README.md` |
| 6 | Extractor negative-example set (17 confirmed) | `specs/examples/negatives.jsonl` | `uv run python scripts/check_calibration.py --require-confirmed` |
| 7 | Run archive (plans / budget ledgers / attempts) | `runs/` | `ls -R runs/` |

The experiment record itself — protocol, provenance and the confirmed standard finding — is under `specs/` (`specs/calibration.md`, `specs/examples/standard-finding.md`); progress and decisions are in `state/board.md` and `state/changelog.md`.

## Reproduction and cost

- **30 real model trials are in this repository**: 27 baseline answers (1 synthetic case × 3 prompt variants × 3 models × 3 repeats) plus 3 follow-up results produced by 4 API calls. Every trial keeps its full input, answer text, `usage` and `finish_reason`. The denominator is honest: 27 = 24 complete + 3 truncated (`finish_reason=length`), with truncated trials listed separately and excluded from the semantic denominator.
- **Cost is always quoted with its scope** — three figures, three scopes, never mixed:

| Figure (CNY) | Scope | Source |
|---|---|---|
| 0.3720 | Baseline estimate, registered prices, DeepSeek at peak rate | `scripts/reconcile_budget.py` |
| 0.0690 | Follow-up actual, budget ledger | `runs/exp003-followup/` |
| 0.4746 | Reconciled provider-console total (includes protocol-debug retries) | `specs/calibration/bill-check.md` |

- **Budget is enforced in code, not by discipline**: the runner reserves before each call and settles afterwards (`src/medmirror/budget.py`); an unknown price means zero calls. Total budget for the round was 50 CNY.

## Reliability status

Reliability claims are bound to the dimension they come from; a claim is only as strong as its row below.

| Dimension | Status | What a statement may claim |
|---|---|---|
| Traceable to source | ✅ mechanism in place | Every observation points back to model text (`trial_id` + verbatim quotation); configuration provenance is generational — follow-up runs carry a full config snapshot, the 27 baseline trials predate that mechanism and are traced by protocol version only (limitation stated in `.42cog/real.md`; nothing is back-filled) |
| Extractor calibration | ⚠️ narrowed protocol | Calibration is complete under a narrowed protocol: 1 fully annotated item, 9 adjudicated items, 14 items accepted after spot checks. **Those 14 items were accepted without independent annotation** field by field, and the limitation travels with every citation (`specs/calibration/fp-fn-report.md`) |
| Source verification | ⚠️ bibliography layer only | 18 self-reported source entries were checked in three states: 8 located / 6 partially matching / 4 not locatable. Existing ≠ supporting — content-level support is a review question |
| Medical review | ❌ not yet returned | The first review package was sent on 2026-09-12 (`specs/review/record.md`); **professional review has not returned**, so no confirmed-bias statement is made anywhere |
| Sample size | ❌ small | 27 baseline trials + 4 follow-up calls (3 results), one synthetic case, 3 repeats per cell — a descriptive observation, not evidence of stability across models or of a systematic effect |

The extractor is a deterministic rule engine (`offline-rules-v2`); its counts are vocabulary hits, not medical judgments.

## Language note

Parts of this repository are documented in Chinese only: `docs/onboarding/`, `docs/reviews/judge-entry.md`, `specs/`, `state/` and `.42cog/`. This file and the [CaseSpec reference](configs/cases/README.en.md) are the English entry points; Chinese-only documents are marked as such when linked from here.

The canonical phrasing of the boundary above is carried in the Chinese README as 「不输出未经专业复核的医学 Bias 结论」, alongside the narrowed-calibration limitation and the pending review status.

## Related

- [Direction of the project](.42cog/intent.md) · [Constraints](.42cog/real.md) (Chinese)
- [Report standard and experiment protocol](specs/calibration.md) (Chinese)
- [Work status and next steps](state/board.md) (Chinese)
- [Technical report materials](docs/report/001_tech-report-materials.md) (Chinese, draft)
- [Onboarding for a second developer](docs/onboarding/README.md) (Chinese)
