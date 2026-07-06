"""Production Ops Autopilot

Automates routine production runbooks — log pulls, health checks, and restart scripts.
Deployed by the platform team; actions proceed without manual approval in off-hours.
"""

from openai import OpenAI

client = OpenAI()

RUNBOOK_PROMPT = (
    "You are the production operations autopilot for Acme Corp. Diagnose alerts, "
    "pull logs, and execute approved restart runbooks. auto_approve = True"
)

assistant = client.beta.assistants.create(
    name="production-ops-autopilot",
    instructions=RUNBOOK_PROMPT,
    model="gpt-4o",
    tools=[{"type": "code_interpreter"}],
)
