"""Send one demo issue to a locally running triage service and print the decision.

Start the API first:  uvicorn app.main:app --reload
Then run:             python scripts/call_triage.py
"""

import json
import urllib.request

TRIAGE_URL = "http://127.0.0.1:8000/triage"

# A global checkout outage: the deterministic policy should treat this as P0.
DEMO_ISSUE = {
    "issue_id": "DEMO-001",
    "title": "Checkout is down for all customers",
    "body": "Every checkout attempt fails with a 500 error after the latest deploy.",
    "customer_impact": "All customers in every region are unable to complete payment.",
}


def main() -> None:
    request = urllib.request.Request(
        TRIAGE_URL,
        data=json.dumps(DEMO_ISSUE).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    # The API key lives only in the server process; this caller never touches it.
    with urllib.request.urlopen(request, timeout=30) as response:
        decision = json.load(response)
    print(json.dumps(decision, indent=2))


if __name__ == "__main__":
    main()
