#!/usr/bin/env python3
"""运行 exp001：固定离线样本，不调用外部 API。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from medmirror.protocol import aggregate, extract_trial, load_jsonl, render_report, validate_contract


def main() -> int:
    exp = ROOT / "docs/experiments/exp001-protocol-smoke"
    fixture_path = exp / "fixtures.jsonl"
    output_dir = exp / "result"
    output_dir.mkdir(parents=True, exist_ok=True)
    trials = load_jsonl(fixture_path)
    extractions = [extract_trial(trial) for trial in trials]
    summary = aggregate(trials, extractions)
    errors = validate_contract(trials, extractions, summary)
    (output_dir / "extractions.jsonl").write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in extractions) + "\n")
    (output_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    (output_dir / "report.md").write_text(render_report(summary, extractions, errors))
    print(render_report(summary, extractions, errors), end="")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
