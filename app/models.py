from typing import Literal

from pydantic import BaseModel, Field

# Closed vocabularies keep every layer speaking the same triage language.
Priority = Literal["P0", "P1", "P2", "P3"]
RoutingTeam = Literal["security", "payments", "reliability", "platform", "product-support"]
DecisionSource = Literal["baseline", "human_override", "model-assisted", "baseline_fallback"]


# A decision a person has already made; automation must not overrule it.
class HumanOverride(BaseModel):
    priority: Priority
    routing_team: RoutingTeam
    reason: str = Field(min_length=1)


# An incoming support issue as received by the API.
class Issue(BaseModel):
    issue_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    body: str
    customer_impact: str = ""
    human_override: HumanOverride | None = None


# The only shape a model response may take once it crosses the provider boundary.
class ModelSuggestion(BaseModel):
    priority: Priority
    routing_team: RoutingTeam
    summary: str


# The final, auditable outcome returned to callers.
class TriageDecision(BaseModel):
    issue_id: str
    priority: Priority
    routing_team: RoutingTeam
    requires_human_review: bool
    decision_source: DecisionSource
    summary: str
