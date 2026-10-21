"""Tier A: the deterministic policy alone must reproduce every frozen label.

No API key and no network access are needed.
"""

import unittest

from app.triage_rules import classify_issue
from evals.helpers import compared_fields, load_cases

EXPECTED_CASE_COUNT = 10


class TierADeterministicPolicyTest(unittest.TestCase):
    def setUp(self) -> None:
        self.cases = load_cases()

    def test_fixture_contains_all_frozen_cases(self) -> None:
        self.assertEqual(len(self.cases), EXPECTED_CASE_COUNT)

    def test_baseline_matches_frozen_labels(self) -> None:
        for case in self.cases:
            with self.subTest(issue_id=case.issue.issue_id):
                decision = classify_issue(case.issue)
                self.assertEqual(compared_fields(decision), case.expected, case.issue.issue_id)


if __name__ == "__main__":
    unittest.main()
