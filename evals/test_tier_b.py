"""Tier B: the orchestrator must keep its guardrails around a model provider.

A controlled stub replaces Gemini, so no API key and no network access are needed.
"""

import unittest

from app.model_provider import ModelProviderError
from app.models import Issue, ModelSuggestion, TriageDecision
from app.orchestrator import PROVIDER_UNAVAILABLE_NOTE, TriageOrchestrator
from evals.helpers import EvalCase, compared_fields, load_cases

DOWNGRADE_ISSUE_ID = "ISSUE-001"
FAILING_ISSUE_ID = "ISSUE-006"
OVERRIDE_ISSUE_ID = "ISSUE-010"


class StubModelProvider:
    """Deterministic stand-in for a model, with one unsafe and one failing case."""

    def __init__(self, cases: list[EvalCase]) -> None:
        self._expected = {case.issue.issue_id: case.expected for case in cases}
        self.calls: list[str] = []

    def suggest(self, issue: Issue) -> ModelSuggestion:
        self.calls.append(issue.issue_id)
        if issue.issue_id == DOWNGRADE_ISSUE_ID:
            return ModelSuggestion(
                priority="P3",
                routing_team="product-support",
                summary="Stub: looks routine.",
            )
        if issue.issue_id == FAILING_ISSUE_ID:
            raise ModelProviderError("Stub: provider unavailable.")
        expected = self._expected[issue.issue_id]
        return ModelSuggestion(
            priority=expected["priority"],
            routing_team=expected["routing_team"],
            summary=f"Stub suggestion for {issue.issue_id}.",
        )


def _expected_source(issue_id: str) -> str:
    if issue_id == OVERRIDE_ISSUE_ID:
        return "human_override"
    if issue_id == FAILING_ISSUE_ID:
        return "baseline_fallback"
    return "model-assisted"


class TierBGuardedOrchestrationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.cases = {case.issue.issue_id: case for case in load_cases()}
        self.provider = StubModelProvider(list(self.cases.values()))
        self.orchestrator = TriageOrchestrator(self.provider)

    # Report an escaped provider error as a guardrail failure, not a crash.
    def _triage(self, issue_id: str) -> TriageDecision:
        try:
            return self.orchestrator.triage(self.cases[issue_id].issue)
        except ModelProviderError as error:
            self.fail(f"{issue_id}: provider failure escaped the orchestrator ({error}).")

    def _assert_frozen_labels(self, issue_id: str, decision: TriageDecision) -> None:
        self.assertEqual(compared_fields(decision), self.cases[issue_id].expected, issue_id)

    def test_human_override_bypasses_provider(self) -> None:
        decision = self._triage(OVERRIDE_ISSUE_ID)

        self.assertNotIn(OVERRIDE_ISSUE_ID, self.provider.calls, "Provider was called for an override.")
        self.assertEqual(decision.decision_source, "human_override", OVERRIDE_ISSUE_ID)
        self._assert_frozen_labels(OVERRIDE_ISSUE_ID, decision)

    def test_provider_failure_returns_baseline_fallback(self) -> None:
        decision = self._triage(FAILING_ISSUE_ID)

        self.assertEqual(decision.decision_source, "baseline_fallback", FAILING_ISSUE_ID)
        self.assertIn(PROVIDER_UNAVAILABLE_NOTE, decision.summary, FAILING_ISSUE_ID)
        self._assert_frozen_labels(FAILING_ISSUE_ID, decision)

    def test_unsafe_downgrade_is_rejected(self) -> None:
        decision = self._triage(DOWNGRADE_ISSUE_ID)

        self.assertIn(DOWNGRADE_ISSUE_ID, self.provider.calls)
        self.assertEqual(decision.decision_source, "model-assisted", DOWNGRADE_ISSUE_ID)
        self._assert_frozen_labels(DOWNGRADE_ISSUE_ID, decision)

    def test_all_guarded_outcomes_preserve_frozen_labels(self) -> None:
        for issue_id in self.cases:
            with self.subTest(issue_id=issue_id):
                decision = self._triage(issue_id)
                self.assertEqual(decision.decision_source, _expected_source(issue_id), issue_id)
                self._assert_frozen_labels(issue_id, decision)

        self.assertNotIn(OVERRIDE_ISSUE_ID, self.provider.calls, "Provider was called for an override.")


if __name__ == "__main__":
    unittest.main()
