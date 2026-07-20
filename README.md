# AgentShadow

## Agent Security Posture Management (ASPM)

AgentShadow is an open-source Agent Security Posture Management platform that provides visibility, governance, and security controls for autonomous AI agents, agent frameworks, and Model Context Protocol (MCP) environments.

As organizations deploy AI agents with increasing autonomy, AgentShadow helps security teams understand what agents exist, what tools they can access, and how they should be governed.

---

## Why AgentShadow?

AI agents can:

- Execute workflows
- Access sensitive systems
- Invoke APIs
- Use external tools
- Make autonomous decisions

Organizations need visibility before they can secure them.

AgentShadow provides that foundation.

---

## Key Features

- Agent Discovery
- Agent Inventory
- Tool Permission Analysis
- Governance Policies
- Risk Scoring
- MCP Visibility
- REST API
- Dashboard

---

## Example Use Cases

- AI Agent Governance
- MCP Security
- AI Agent Inventory
- AI Risk Assessment
- Autonomous Workflow Security
- Research

---

## Architecture

```
AI Agents
       │
       ▼
Discovery Engine
       │
       ▼
Inventory
       │
       ├── Risk Engine
       ├── Policy Engine
       ├── Governance
       └── Reporting
```

---

## Roadmap

- Agent Trust Graph
- Tool Risk Analysis
- Runtime Governance
- Human Approval Policies
- Enterprise Connectors
- Agent Behavior Analytics
- AI Supply Chain Visibility

---

## Enterprise Platform

The commercial AgentShadow platform adds:

- Enterprise Governance
- Multi-tenancy
- RBAC
- Enterprise Dashboards
- SIEM Integrations
- Compliance Reporting
- Continuous Monitoring
- Commercial Support

---

## Quick start (Docker)

```bash
# macOS / Linux
./start.sh

# Windows (double-click, or from cmd/PowerShell in this folder)
start.bat
```

Or with Compose directly:

```bash
cp .env.example .env
docker compose up --build
# API http://localhost:8013 · UI http://localhost:3011
```

---

## Vision

AgentShadow is part of the Valo Security Platform, providing comprehensive visibility, governance, and enforcement across AI prompts, models, SaaS applications, and autonomous AI agents.

---

## Contributing

Community contributions are encouraged.

---

## License

Apache 2.0

---

## Learn More

https://valosecurity.ai
