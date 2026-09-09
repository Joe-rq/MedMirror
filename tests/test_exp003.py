import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from run_exp003_baseline import VARIANTS, planned_trials
from medmirror.providers import model_registry


class Exp003PlanTest(unittest.TestCase):
    def test_small_batch_has_nine_unique_trials(self):
        trials = planned_trials(model_registry(), 1)
        self.assertEqual(len(trials), 9)
        self.assertEqual(len({trial["trial_id"] for trial in trials}), 9)
        self.assertEqual({trial["prompt_variant"] for trial in trials}, set(VARIANTS))

    def test_full_protocol_has_twenty_seven_trials(self):
        self.assertEqual(len(planned_trials(model_registry(), 3)), 27)


if __name__ == "__main__":
    unittest.main()
