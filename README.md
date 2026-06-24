# 🔐 Gatekeeper — AI Trust Gateway

> *"The competition logs what your AI did. Gatekeeper controls what your AI is allowed to do."*

**Gatekeeper** is a real-time AI governance middleware that sits between any AI agent and a client environment. Before a single command runs, Gatekeeper evaluates it, approves or blocks it, logs it with a cryptographic signature, and generates a legally defensible audit report on exit.

Built by **Oscar Reyes Luna** · Everforth Innovation Labs · Apex Systems  
**Everforth Galactic Hackathon 2026 — Grand Finalist**

---

## 🚀 Live Demo

**→ [http://18.216.220.211:8001](http://18.216.220.211:8001)**

| Service | URL |
|---|---|
| Gatekeeper (AI Trust Gateway) | http://18.216.220.211:8001 |
| ScoutAgent (AI Infrastructure Scanner) | http://18.216.220.211:7070 |

---

## 💡 The Problem — Millions Sitting Idle

Enterprise has 60–70 AI projects built, tested, and ready — going nowhere.  
Not because they don't work. Because no enterprise client will let an unmonitored AI touch their network.

Every day those projects sit idle, revenue walks out the door.  
Enterprise buyers don't say "no" to AI. They say "prove it's safe."

**Gatekeeper is the proof.**

---

## ✅ The Solution — Four Pillars

```
┌─────────────────────────────────────────────────────────────┐
│  GOVERN — Every AI action approved before it runs           │
│  Agent declares scope → Operator reviews → Gatekeeper logs  │
├─────────────────────────────────────────────────────────────┤
│  AUDIT — Every action has a receipt                         │
│  SHA-256 signed trail · tamper-evident · legally defensible │
├─────────────────────────────────────────────────────────────┤
│  COMPLY — CIS Controls v8 + NIST SP 800-53 built in        │
│  Automatic compliance documentation per session             │
├─────────────────────────────────────────────────────────────┤
│  DEPLOY — Runs on AWS Bedrock                               │
│  Data never leaves your AWS environment · IAM role auth     │
└─────────────────────────────────────────────────────────────┘
```

---

## 💰 Business Model — Governance You Can Sell

| Revenue Stream | Detail |
|---|---|
| **Premium Compliance Tier** | Package Gatekeeper as an enterprise add-on on every AI deployment |
| **Auditable AI Upsell** | Clients pay a premium for signed, lawyer-ready audit reports |
| **Regulatory Documentation** | EU AI Act + NIST AI RMF require AI governance docs — we generate them automatically |
| **Market Unlock** | Opens government + regulated industry contracts previously closed to AI tools |
| **Audit Fee Savings** | Replaces $50K–$200K/yr in third-party AI compliance audits |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CLIENT BROWSER                           │
│              Gatekeeper Approval UI (:8001)                 │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                 GATEKEEPER API (FastAPI)                     │
│  /session/start    → register agent + requested scope       │
│  /session/approve  → operator reviews and approves          │
│  /access/request   → evaluate + allow/block in real time    │
│  /session/exit     → generate signed PDF audit report       │
└────────┬─────────────────┬────────────────────┬────────────┘
         │                 │                    │
┌────────▼──────┐  ┌───────▼────────┐  ┌───────▼──────────┐
│  AWS BEDROCK  │  │   SQLite DB    │  │  WeasyPrint PDF  │
│  Claude 4.6   │  │  Sessions +    │  │  SHA-256 signed  │
│  via IAM Role │  │  Access Logs   │  │  Audit Reports   │
│  (no API keys)│  └────────────────┘  └──────────────────┘
└───────────────┘
         │
┌────────▼──────────────────────────────────────────────────┐
│                   ScoutAgent 2.0                          │
│  AI Infrastructure Scanner — every tool call gated here   │
└───────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| Backend API | Python 3.14 + FastAPI |
| AI Engine | Claude Sonnet 4.6 via AWS Bedrock |
| Authentication | IAM Role — no hardcoded credentials, auto-rotating |
| Database | SQLite |
| PDF Generation | WeasyPrint — pixel-perfect branded reports |
| Audit Integrity | SHA-256 cryptographic hash per session |
| Frontend | Vanilla HTML/CSS/JS |
| Deployment | AWS EC2 · Ubuntu · systemd service |
| Security Standards | CIS Controls v8 · NIST SP 800-53 |

---

## ⚡ Quick Start

```bash
git clone https://github.com/Calo0420/Gatekeeper.git
cd Gatekeeper

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configure AWS Bedrock
export DEPLOY_MODE=bedrock
export BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-6
# Attach ec2-bedrock-role IAM role to your EC2 instance

uvicorn main:app --host 0.0.0.0 --port 8001
```

Open `http://localhost:8001`

---

## 🔌 API Reference

### Start a Session
```http
POST /session/start
{
  "agent_id": "scout-001",
  "agent_name": "ScoutAgent",
  "requested_scope": ["scan_linux_environment", "check_cis_benchmarks", "generate_executive_report"]
}
```

### Approve a Session
```http
POST /session/approve
{
  "session_id": "1B6A86A4",
  "approved_by": "Operator",
  "approved_scope": ["scan_linux_environment", "check_cis_benchmarks", "generate_executive_report"]
}
```

### Request Access (called by AI agent per tool call)
```http
POST /access/request
{
  "session_id": "1B6A86A4",
  "token": "GK-1B6A86A4-TOKEN",
  "resource": "scan_linux_environment",
  "action": "execute"
}
```

Response:
```json
{ "allowed": true, "reason": "Within approved scope" }
```

### Close Session + Generate Audit Report
```http
POST /session/exit
{ "session_id": "1B6A86A4", "token": "GK-1B6A86A4-TOKEN" }
```

### Download PDF Audit Report
```http
GET /session/{session_id}/report
```

---

## 📄 Sample Audit Report Output

```
GATEKEEPER — AI TRUST AUDIT REPORT
Everforth Innovation Labs

Session ID:    602BB624
Agent:         ScoutAgent (scout-001)
Approved By:   Operator
Start:         2026-06-24T10:10:33 UTC
Exit:          2026-06-24T10:13:06 UTC

APPROVED SCOPE:
  • scan_linux_environment
  • check_cis_benchmarks
  • scan_windows_environment
  • generate_executive_report

ACCESS LOG:
  ALLOWED   scan_windows_environment    execute   10:10:43
  ALLOWED   check_windows_security      execute   10:11:11
  ALLOWED   generate_executive_report   execute   10:11:51

Total Requests: 3 | Blocked: 0
EXIT STATUS: CLEAN DISCONNECTION CONFIRMED

Audit Hash (SHA-256):
91c3730580dc27778e205f80b2a2ecc40955a35462630389d59842ea73f8e1d3

Generated: 2026-06-24T10:13:06 UTC
```

---

## 🆚 Why Not the Competition?

| Solution | Blocks before execution? | Signed PDF audit? | Any AI agent? | On Bedrock? |
|---|---|---|---|---|
| **Gatekeeper** | ✅ | ✅ | ✅ | ✅ |
| Guardrails AI | ❌ | ❌ | Partial | ❌ |
| LangSmith | ❌ logs after | ❌ | LangChain only | ❌ |
| Microsoft Purview | ❌ | ❌ | Microsoft only | ❌ |
| Salesforce Trust Layer | ❌ | ❌ | Salesforce only | ❌ |

---

## 🗺️ Roadmap

| Phase | Status | Features |
|---|---|---|
| Core MVP | ✅ Live | Approval UI, real-time monitor, SHA-256 signed PDF, ScoutAgent integration |
| AWS Bedrock | ✅ Live | Claude Sonnet 4.6 via Bedrock, IAM role, zero data leakage |
| Windows Support | ✅ Live | WinRM scanning fully governed and audited |
| Multi-Agent | 🔜 Next | Multiple simultaneous AI agents per session |
| Enterprise Portal | 🔜 Next | Client dashboard, SSO, role-based approval workflows |
| ServiceNow Integration | 🔜 Future | Auto-create change tickets from audit events |

---

## 👤 Author

**Oscar Reyes Luna** (Calo0420)  
Technical Consultant · Everforth Innovation Labs · Apex Systems  
Querétaro, Mexico

---

## 📜 License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">
  <sub>Gatekeeper · Everforth Innovation Labs · Apex Systems · Galactic Hackathon 2026 Grand Finalist</sub>
</div>
