import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from medmirror.protocol import aggregate, extract_trial, load_jsonl, validate_contract


class Exp001ContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = ROOT / "docs/experiments/exp001-protocol-smoke/fixtures.jsonl"
        cls.trials = load_jsonl(path)
        cls.extractions = [extract_trial(trial) for trial in cls.trials]
        cls.summary = aggregate(cls.trials, cls.extractions)

    def test_failed_trial_is_not_unmentioned(self):
        failed = next(row for row in self.extractions if row["trial_id"] == "smoke-006")
        self.assertEqual(failed["status"], "error")
        self.assertEqual(self.summary["valid_n"], 5)
        self.assertEqual(self.summary["failed_n"], 1)
        self.assertEqual(self.summary["path_rates"]["tcm"]["valid_n"], 5)

    def test_semantic_states_are_separate(self):
        by_id = {row["trial_id"]: row for row in self.extractions}
        self.assertEqual(by_id["smoke-002"]["paths"]["tcm"]["state"], "opposed")
        self.assertEqual(by_id["smoke-003"]["paths"]["tcm"]["state"], "conditional_support")
        self.assertEqual(by_id["smoke-004"]["paths"]["western"]["state"], "recommended")

    def test_evidence_mentioned_is_not_evidence_verified(self):
        row = next(row for row in self.extractions if row["trial_id"] == "smoke-005")
        self.assertTrue(row["evidence_mentioned"])
        self.assertFalse(row["identifiable_source"])

    def test_contract_passes(self):
        self.assertEqual(validate_contract(self.trials, self.extractions, self.summary), [])


if __name__ == "__main__":
    unittest.main()
