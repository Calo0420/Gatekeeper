import json
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from db import get_db

router = APIRouter()

class AccessRequest(BaseModel):
    session_id: str
    token: str
    resource: str
    action: str

@router.post("/request")
def request_access(req: AccessRequest):
    db = get_db()
    session = db.execute(
        "SELECT * FROM sessions WHERE session_id=? AND status='active'",
        (req.session_id,)).fetchone()
    if not session:
        raise HTTPException(403, "Invalid or inactive session")
    approved_scope = json.loads(session["approved_scope"])
    allowed = req.resource in approved_scope
    reason = "Within approved scope" if allowed else "Resource not in approved scope — BLOCKED"
    db.execute("""INSERT INTO access_logs
        (session_id, resource, action, allowed, reason, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)""",
        (req.session_id, req.resource, req.action,
         1 if allowed else 0, reason, datetime.utcnow().isoformat()))
    db.commit()
    db.close()
    return {"allowed": allowed, "reason": reason, "resource": req.resource}
