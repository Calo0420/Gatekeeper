# Gatekeeper — AI Trust Gateway

Gatekeeper is a governance layer that sits between an AI agent and a client's environment. A human must authorize a session before it runs, every access request is evaluated in real time against policy, and every session closes with a signed audit trail that can be independently re-verified from the raw logs.

Built by Oscar Reyes Luna, Everforth Innovation Labs, as part of the ScoutAgent 2.0 accelerator.

---

## How this is actually used

Gatekeeper is not sold as a standalone product. It is an internal tool used alongside ScoutAgent 2.0 during client engagements: a scan runs against a prospective or existing client's environment, Gatekeeper governs and logs exactly what that scan touched, and the resulting findings and audit report are what the engagement is built around. The value isn't the license, it's the assessment and the consulting work that follows it. Gatekeeper is the reason a client is willing to let that scan happen against production infrastructure in the first place.

---

## Where this actually fits

AI agent governance is not an empty category. Microsoft publishes an open source Agent Governance Toolkit doing policy enforcement, identity, and tamper-evident audit logging across a dozen agent frameworks. Several other open source projects in this space use stronger primitives than Gatekeeper does today, hash-chained ledgers, formally verified state machines, asymmetric signing.

What Gatekeeper is not trying to be is a general-purpose governance platform for any agent framework. It is a purpose-built trust gate for one specific workflow: an AI-driven infrastructure scan against a client's live environment, with a human approval step and a signed report that a client's own security team can verify without taking anyone's word for it. That is a narrower claim than "the only AI trust gateway," and it's the honest one.

---

## What it actually does

**Session approval.** ScoutAgent registers a session and its requested scope. Nothing runs until a human clicks Authorize in the Gatekeeper UI and supplies the operator token, a shared secret that ScoutAgent itself never has access to, so the AI agent cannot self-approve its own session under any circumstance. If the operator token isn't configured on the server at all, approval is refused outright rather than falling back to an open door.

**Real-time policy enforcement.** Every file access and service interaction the agent attempts is evaluated against a policy engine aligned to CIS Controls v8 and NIST SP 800-53. Credential files are detected but their contents are never read, enforced at the gateway, not left to the model's judgment. If Gatekeeper itself becomes unreachable, mid-scan, timeout, connection refused, server error, every pending and subsequent request is denied by default.

**Signed, independently verifiable audit trail.** Every session closes with a report showing exactly what was requested, what was allowed, and what was blocked. When `GATEKEEPER_AUDIT_KEY` is configured, the report is signed with HMAC-SHA256, an attacker with database or report-file access cannot forge a matching hash without also knowing that key, which lives only in the server's environment, never in the database or in any report file. Without the key configured, reports still generate and are labeled honestly as unkeyed, since a hash without a key is real evidence of accidental corruption but not of deliberate tampering by anyone with write access to the data.

---

## Architecture

```
Client Browser
      |
      v
+-----------------------------------+
|     GATEKEEPER API (FastAPI)      |
|  /session/start   -> register     |
|  /session/approve -> human-gated  |
|  /access/request  -> policy check |
|  /session/exit    -> signed PDF   |
+----------------+-------------------+
                 |
        +--------+---------+
        |                  |
   SQLite DB          ReportLab PDF
   (sessions,         (HMAC-signed
    access logs)       when keyed)
                 |
        +--------+---------+
        |                  |
   ScoutAgent          Approval UI
   (real scan agent,   (operator-token
    real API calls)     gated)
```

---

## Tech stack

| Component | Technology |
|-----------|-----------|
| Backend API | Python + FastAPI |
| Database | SQLite |
| PDF generation | ReportLab |
| Audit integrity | HMAC-SHA256 when `GATEKEEPER_AUDIT_KEY` is set, plain SHA-256 otherwise, always labeled honestly, independently re-verifiable via `verify_audit.py` |
| Session approval | Operator-token gated, constant-time comparison, fails closed if unconfigured |
| Frontend | Vanilla HTML/CSS/JS |
| AI risk analysis | AWS Bedrock (Claude Sonnet 4.6), or direct Anthropic API, Azure OpenAI, or a fully local model, selected per engagement |

---

## Quick start

```bash
git clone git@github.com:Calo0420/Gatekeeper.git
cd Gatekeeper

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Set OPERATOR_PASSWORD-equivalent security values before running:
#   GATEKEEPER_OPERATOR_TOKEN  — required for /session/approve to work at all
#   GATEKEEPER_AUDIT_KEY       — optional but strongly recommended, generate with:
#                                 python3 -c "import secrets; print(secrets.token_urlsafe(32))"

uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

Open `http://localhost:8001` in a browser.

---

## API reference

### Start a session
```http
POST /session/start
Content-Type: application/json

{
  "agent_id": "scout-001",
  "agent_name": "ScoutAgent",
  "requested_scope": ["scan_linux_environment", "check_cis_benchmarks"]
}
```

### Approve a session
Requires the operator token, held only by the human reviewing the request in the browser, never by ScoutAgent itself.
```http
POST /session/approve
Content-Type: application/json
X-Operator-Token: <the configured GATEKEEPER_OPERATOR_TOKEN>

{
  "session_id": "1B6A86A4",
  "approved_by": "Operator",
  "approved_scope": ["scan_linux_environment", "check_cis_benchmarks"]
}
```

### Request access to a resource
```http
POST /access/request
Content-Type: application/json

{
  "session_id": "1B6A86A4",
  "token": "GK-1B6A86A4-TOKEN",
  "resource": "/opt/client-app/.env",
  "action": "read"
}
```

Response, credential files are detected as in-scope but reads are still blocked at the policy layer regardless of session approval:
```json
{
  "allowed": false,
  "reason": "Credential file detected — read blocked by policy (CIS Control 3)",
  "resource": "/opt/client-app/.env"
}
```

### Close session and generate the report
```http
POST /session/exit
Content-Type: application/json

{
  "session_id": "1B6A86A4",
  "token": "GK-1B6A86A4-TOKEN"
}
```

### Download the signed audit report
```http
GET /session/{session_id}/report
```

---

## Verify a report yourself

The audit hash is not a claim to be trusted, it's math a client's own security team can rerun independently.

```bash
python3 verify_audit.py <SESSION_ID>
#   hash mode   : hmac-sha256   (or sha256-unkeyed, with a warning, if no key is configured)
#   OK  MATCH    — audit integrity verified
#   !!  MISMATCH — the access record was altered after signing
```

This was tested for real, not just designed on paper: a blocked access entry was deliberately flipped to allowed directly in the database, and `verify_audit.py` correctly reported a mismatch with a recomputed hash that genuinely differed from the issued one. The database was restored and verification passed cleanly again afterward.

---

## Current state

Live and integrated with a real ScoutAgent 2.0 scan, not mocked. Every code path referenced in this document has been live-tested against a running instance: session approval bypass attempts (no token, wrong token, unconfigured server) all correctly denied; database tampering correctly detected by the audit verifier; dependency scan clean on all pinned packages as of the most recent check.

---

## Roadmap

| Status | Item |
|--------|------|
| Done | Operator-token gated approval, fails closed |
| Done | HMAC-SHA256 audit signing with honest fallback labeling |
| Done | Real ScoutAgent integration, AI risk analysis via AWS Bedrock |
| Next | Hash-chained audit ledger rather than a single per-session hash |
| Next | Role-based access instead of one shared operator secret |
| Later | Multi-agent session support, client-facing portal |

---

## License

MIT License, see [LICENSE](LICENSE).
