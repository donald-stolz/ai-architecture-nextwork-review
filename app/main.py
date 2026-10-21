from fastapi import FastAPI

from app.models import Issue, TriageDecision
from app.orchestrator import build_orchestrator

# Create the HTTP API and the guarded orchestrator it delegates to.
app = FastAPI(title="Support Issue Triage Service")
orchestrator = build_orchestrator()


# A sync handler runs in FastAPI's thread pool, so the blocking model call is safe here.
@app.post("/triage", response_model=TriageDecision)
def triage(issue: Issue) -> TriageDecision:
    return orchestrator.triage(issue)
