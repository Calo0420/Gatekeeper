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
import hmac
import json
import os

from dotenv import load_dotenv
load_dotenv()  # standalone scripts (verify_audit.py) may import this module
                # directly without going through db.py's load_dotenv() side effect


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


def hash_mode() -> str:
    """Which mode compute_hash() will actually use, so callers can label the
    report honestly instead of claiming stronger tamper evidence than what's
    actually configured."""
    return "hmac-sha256" if os.getenv("GATEKEEPER_AUDIT_KEY", "") else "sha256-unkeyed"


def compute_hash(session_id, logs):
    """
    The audit hash.

    A PLAIN hash (hashlib.sha256 with no key) can be forged by anyone with
    database write access: they tamper the row, recompute the same public
    function themselves, and the result matches their tampered data. It
    only ever proved the report matched the DB at generation time, not
    that either one is trustworthy.

    When GATEKEEPER_AUDIT_KEY is configured, this uses HMAC-SHA256 instead —
    an attacker with DB or filesystem access still cannot produce a valid
    hash for tampered data without also knowing the key, which lives only
    in .env, never in the database or the report files.

    Falls back to the plain (unkeyed) hash when no key is configured, so
    report generation never breaks — but hash_mode() tells the caller which
    one actually happened, and report_generator.py labels the report
    accordingly rather than overstating what protection is in place.

    Honest limitation, stated plainly: this protects against tampering via
    database or report-file access alone. An attacker with full server
    filesystem access can also read GATEKEEPER_AUDIT_KEY from .env. That is
    a materially different, larger threat model and isn't what this fix
    claims to solve.
    """
    payload = canonical_payload(session_id, logs).encode("utf-8")
    key = os.getenv("GATEKEEPER_AUDIT_KEY", "")
    if key:
        return hmac.new(key.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    return hashlib.sha256(payload).hexdigest()
