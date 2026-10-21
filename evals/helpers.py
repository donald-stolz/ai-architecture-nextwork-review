import json
from pathlib import Path
from typing import Any, NamedTuple

from app.models import Issue

FIXTURE_PATH = Path(__file__).with_name("issues.json")

# The fields every evaluation compares against the frozen labels.
COMPARED_FIELDS = ("priority", "routing_team", "requires_human_review")


class EvalCase(NamedTuple):
    issue: Issue
    expected: dict[str, Any]


def load_cases() -> list[EvalCase]:
    """Load and validate every frozen case from evals/issues.json."""
    records = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    return [
        EvalCase(issue=Issue.model_validate(record["issue"]), expected=dict(record["expected"]))
        for record in records
    ]


def compared_fields(decision: Any) -> dict[str, Any]:
    """Project a TriageDecision onto the fields the fixture labels."""
    return {field: getattr(decision, field) for field in COMPARED_FIELDS}
