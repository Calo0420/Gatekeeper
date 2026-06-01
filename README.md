# 🔐 Gatekeeper — AI Trust Gateway

> *"Every AI deployment runs on trust me bro. This is the receipt."*

**Gatekeeper** is a middleware trust layer that sits between any AI agent and a client environment. It enforces approved access scope, monitors every data request in real time, blocks unauthorized access automatically, and generates a cryptographically signed audit report on clean exit.

Built by **Rogue Protocol** for the **Everforth Galactic Hackathon 2026**.

---

## 🎯 The Problem

Every AI agent deployed at a client site today operates on verbal trust.

There is no standard proof of what was accessed, what was blocked, or that the agent disconnected cleanly. This single issue blocks the majority of enterprise AI deployments — clients refuse to let AI tools touch their environments because there is no receipt, no audit trail, and no verifiable proof of what happened.

**Consultants say: "trust me."**
**Clients say: no.**

---

## ✅ The Solution

Gatekeeper operates in three phases:

```
┌─────────────────────────────────────────────────────────────┐
│  PHASE 1 — APPROVED ENTRY                                    │
│  Agent declares access scope → Client reviews and approves  │
│  Gatekeeper logs the session contract                        │
├─────────────────────────────────────────────────────────────┤
│  PHASE 2 — MONITORED ACCESS                                  │
│  Every request passes through Gatekeeper                    │
│  In-scope → logged and allowed                              │
│  Out-of-scope → blocked automatically and flagged           │
├─────────────────────────────────────────────────────────────┤
│  PHASE 3 — CERTIFIED EXIT                                    │
│  Agent disconnects → Gatekeeper generates signed PDF report │
│  Session ID · timestamps · access log · SHA-256 hash        │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Live Demo

**→ [http://147.93.135.84:8001](http://147.93.135.84:8001)**

Try it yourself:
1. Open the link — see ScoutAgent requesting access
2. Click **Approve Access**
3. Watch the live scan — three resources allowed, one blocked
4. Click **Exit Session** — audit report generates instantly
5. See the SHA-256 signed receipt

---

## 🎬 Demo Video

**→ [Watch the full demo](https://drive.google.com/file/d/1RtKOd7ZGosIjfbv0P2DvejNA0ZeIZe7D/view?usp=sharing)**

---

## 🏗️ Architecture

```
Client Browser
      │
      ▼
┌─────────────────────────────────┐
│     GATEKEEPER API (FastAPI)    │
│  /session/start   → log contract│
│  /access/request  → log + block │
│  /session/exit    → generate PDF│
└──────────────┬──────────────────┘
               │
       ┌───────┴────────┐
       │                │
  SQLite DB        ReportLab PDF
  (sessions,       (SHA-256 signed
   access logs)     audit report)
               │
       ┌───────┴────────┐
       │                │
  Mock Agent       Approval UI
  (ScoutAgent       (HTML/JS
   simulator)       frontend)
```

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend API | Python + FastAPI |
| Database | SQLite |
| PDF Generation | ReportLab |
| Audit Integrity | SHA-256 cryptographic hash |
| Frontend | Vanilla HTML/CSS/JS |
| Deployment | Ubuntu VPS |
| Cloud (Phase 2) | AWS Bedrock |

---

## ⚡ Quick Start

```bash
# Clone the repo
git clone https://github.com/Calo0420/Gatekeeper.git
cd Gatekeeper

# Set up environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env

# Run
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

Open `http://localhost:8001` in your browser.

---

## 🔌 API Reference

### Start a Session
```http
POST /session/start
Content-Type: application/json

{
  "agent_id": "scout-001",
  "agent_name": "ScoutAgent",
  "requested_scope": ["network_config.json", "server_inventory.csv"]
}
```

### Approve a Session
```http
POST /session/approve
Content-Type: application/json

{
  "session_id": "1B6A86A4",
  "approved_by": "Oscar",
  "approved_scope": ["network_config.json", "server_inventory.csv"]
}
```

### Request Access to a Resource
```http
POST /access/request
Content-Type: application/json

{
  "session_id": "1B6A86A4",
  "token": "GK-1B6A86A4-TOKEN",
  "resource": "network_config.json",
  "action": "read"
}
```

Response:
```json
{
  "allowed": true,
  "reason": "Within approved scope",
  "resource": "network_config.json"
}
```

### Close Session and Generate Report
```http
POST /session/exit
Content-Type: application/json

{
  "session_id": "1B6A86A4",
  "token": "GK-1B6A86A4-TOKEN"
}
```

### Download Audit Report
```http
GET /session/{session_id}/report
```

Returns a signed PDF audit report.

---

## 🧪 Run the Demo Flow

```bash
# 1. Start a session
curl -s -X POST http://localhost:8001/session/start \
  -H "Content-Type: application/json" \
  -d '{"agent_id":"scout-001","agent_name":"ScoutAgent","requested_scope":["network_config.json","server_inventory.csv","performance_logs.txt"]}' \
  | python3 -m json.tool

# 2. Approve it (replace SESSION_ID)
curl -s -X POST http://localhost:8001/session/approve \
  -H "Content-Type: application/json" \
  -d '{"session_id":"SESSION_ID","approved_by":"Oscar","approved_scope":["network_config.json","server_inventory.csv","performance_logs.txt"]}' \
  | python3 -m json.tool

# 3. Run the mock agent (replace SESSION_ID)
python mock_agent.py SESSION_ID
```

Expected output:
```
[ScoutAgent] Starting scan — Session XXXXXXXX

  [OK     ]  network_config.json
  [OK     ]  server_inventory.csv
  [OK     ]  performance_logs.txt
  [BLOCKED]  employee_salaries.xlsx

[ScoutAgent] Scan complete. Requesting clean exit...

Session closed.
Requests: 4 | Blocked: 1
Audit report: http://localhost:8001/session/XXXXXXXX/report
```

---

## 📄 Sample Audit Report

```
GATEKEEPER — AI TRUST AUDIT REPORT
Everforth Innovation Labs | Rogue Protocol

Session ID:    1B6A86A4
Agent:         ScoutAgent (scout-001)
Approved by:   Oscar
Start:         2026-05-23 05:03:29 UTC
Exit:          2026-05-23 05:03:50 UTC

APPROVED SCOPE:
  • network_config.json
  • server_inventory.csv
  • performance_logs.txt

ACCESS LOG:
  ALLOWED   network_config.json      READ   05:03:45
  ALLOWED   server_inventory.csv     READ   05:03:47
  ALLOWED   performance_logs.txt     READ   05:03:48
  BLOCKED   employee_salaries.xlsx   READ   05:03:49

Total: 4 requests | Blocked: 1
EXIT STATUS: 1 BLOCKED ATTEMPT(S) LOGGED

Audit Hash (SHA-256):
1b23c2f8af7907cce343c5c3c665d0e266fe6f03c4714266b5b29f5aa70592b6

Generated: 2026-05-23T05:03:50 UTC
```

---

## 🗺️ Roadmap

| Phase | Features |
|-------|---------|
| ✅ MVP (now) | Approval UI, live monitor, signed PDF report, mock agent |
| 🔜 Phase 2 | Azure Key Vault signature, AWS Bedrock anomaly detection |
| 🔜 Phase 3 | Multi-agent support, client portal, ServiceNow integration |
| 🔜 Phase 4 | Windows desktop client (Chaperon), enterprise SSO |

---

## 👥 Team

**Rogue Protocol** — Galactic Hackathon 2026

| Name | Role |
|------|------|
| Oscar Reyes Luna | Captain · Builder · Everforth Innovation Labs |

---

## 📜 License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">
  <sub>Built with 🤙 by Rogue Protocol · Everforth Innovation Labs · Galactic Hackathon 2026</sub>
</div>
