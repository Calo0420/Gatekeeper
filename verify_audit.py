#!/usr/bin/env python3
"""
verify_audit.py — independently verify a Gatekeeper session's audit integrity.

Recomputes the SHA-256 over the session's access logs straight from the database,
using the same canonical function the report was signed with, then compares it to
the issued hash (the value printed in the report / stored sidecar).

  MATCH    = the logs are exactly what the report said. Nothing was altered.
  MISMATCH = the access record was changed after the report was signed (tampering).

Usage:
  python3 verify_audit.py <SESSION_ID>
  python3 verify_audit.py <SESSION_ID> --expected <HASH_FROM_REPORT>
"""
import argparse
import json
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from audit import compute_hash

BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, "gatekeeper.db")


def load(session_id, db_path):
    c = sqlite3.connect(db_path)
    c.row_factory = sqlite3.Row
    s = c.execute("SELECT * FROM sessions WHERE session_id=?", (session_id,)).fetchone()
    logs = [dict(r) for r in c.execute(
        "SELECT * FROM access_logs WHERE session_id=? ORDER BY timestamp", (session_id,))]
    c.close()
    return s, logs


def issued_hash(session_id, override):
    if override:
        return override
    p = os.path.join(BASE, "reports", "gatekeeper_%s.audit.json" % session_id)
    if os.path.exists(p):
        with open(p) as f:
            return json.load(f).get("audit_hash")
    return None


def main():
    ap = argparse.ArgumentParser(description="Verify Gatekeeper audit integrity.")
    ap.add_argument("session_id")
    ap.add_argument("--expected", help="hash printed in the issued report")
    ap.add_argument("--db", default=DB, help="path to the access database (default: gatekeeper.db)")
    a = ap.parse_args()

    s, logs = load(a.session_id, a.db)
    if s is None:
        print("  x session %s not found" % a.session_id)
        sys.exit(2)

    recomputed = compute_hash(a.session_id, logs)
    issued = issued_hash(a.session_id, a.expected)
    blocked = sum(1 for l in logs if not l["allowed"])

    print("  session    : %s" % a.session_id)
    print("  log entries : %d  (blocked: %d)" % (len(logs), blocked))
    print("  recomputed  : %s" % recomputed)
    print("  issued      : %s" % (issued or "(no issued hash on file)"))

    if issued is None:
        print("  -> no signed hash to compare against (pre-hash session).")
        sys.exit(0)

    if recomputed == issued:
        print("  OK  MATCH - audit integrity verified. Logs are exactly what was reported.")
        sys.exit(0)

    print("  !!  MISMATCH - TAMPERING DETECTED. The access record no longer matches the signed report.")
    sys.exit(1)


if __name__ == "__main__":
    main()
