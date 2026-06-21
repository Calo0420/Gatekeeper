"""
audit.py — canonical, tamper-evident audit hashing for Gatekeeper sessions.

Hashes the FULL content of every access-log entry (resource, action, decision,
timestamp) plus the session identity — not just counts. Altering *what was
accessed* versus *what was reported* (e.g. flipping a BLOCK to ALLOW, or
rewriting a resource path) changes the hash.

The exact same function is used at report-generation time (report_generator.py)
and by verify_audit.py, so an auditor can independently recompute the hash from
the raw logs and confirm it matches the value printed in the signed report.
"""
import hashlib
import json


def canonical_payload(session_id, logs):
    """Deterministic JSON over the full log content. Order-independent (sorted)."""
    entries = sorted(
        ({
            "resource": l["resource"],
            "action": l["action"],
            "allowed": 1 if l["allowed"] else 0,
            "timestamp": l["timestamp"],
        } for l in logs),
        key=lambda e: (e["timestamp"] or "", e["resource"] or "", e["action"] or "", e["allowed"]),
    )
    return json.dumps(
        {
            "session": session_id,
            "count": len(entries),
            "blocked": sum(1 for e in entries if not e["allowed"]),
            "entries": entries,
        },
        sort_keys=True,
        separators=(",", ":"),
    )


def compute_hash(session_id, logs):
    """SHA-256 of the canonical payload — the tamper-evident audit hash."""
    return hashlib.sha256(canonical_payload(session_id, logs).encode("utf-8")).hexdigest()
