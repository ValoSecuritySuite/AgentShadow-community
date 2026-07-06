"""Seed the AgentShadow Community Edition with demo data.

Scans the bundled `sample_agents/` repository (code discovery) and syncs the
mock OpenAI Assistants connector (runtime discovery), populating the inventory
with a realistic, compelling fleet for demos and screenshots.

This runs at the service layer, so it bypasses the Community Edition upgrade
gate on the runtime-connector HTTP endpoint on purpose: the dashboard ships
pre-populated with a full, impressive fleet (the advert), while interactive
runtime sync stays locked behind an upgrade.

Usage (from the agentshadow-community/ directory, venv active):
    python -m scripts.seed_demo
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.connectors import registry  # noqa: E402
from app.services import inventory_store, scanner  # noqa: E402


def main() -> None:
    inventory_store.init_db()
    cleared = inventory_store.clear_all()
    print(f"Cleared {cleared} existing agent(s).")

    sample_repo = ROOT / "sample_agents"
    code_agents = scanner.scan_repository(str(sample_repo), owner="engineering")
    print(f"Code scan discovered {len(code_agents)} agent(s) from {sample_repo.name}/")

    runtime_agents = registry.sync_connector("openai_assistants", owner="platform-ops")
    print(f"Runtime connector discovered {len(runtime_agents)} agent(s).")

    all_agents = inventory_store.list_agents()
    print(f"\nInventory now holds {len(all_agents)} agent(s):")
    for a in sorted(all_agents, key=lambda x: -x.risk_score):
        print(f"  - {a.name:42s} {a.framework:18s} {a.risk_score:6.1f} {a.risk_level:9s} {a.final_decision}")


if __name__ == "__main__":
    main()
