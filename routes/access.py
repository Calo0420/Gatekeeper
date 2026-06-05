import json
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from db import get_db
from bedrock_analyzer import analyze_blocked_attempt

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

    ai_analysis = None
    if not allowed:
        ai_analysis = analyze_blocked_attempt(
            agent_name=session["agent_name"],
            agent_id=session["agent_id"],
            resource=req.resource,
            action=req.action,
            approved_scope=approved_scope,
            session_id=req.session_id
        )

    db.execute("""INSERT INTO access_logs
        (session_id, resource, action, allowed, reason, ai_analysis, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (req.session_id, req.resource, req.action,
         1 if allowed else 0, reason,
         json.dumps(ai_analysis) if ai_analysis else None,
         datetime.utcnow().isoformat()))
    db.commit()
    db.close()

    result = {"allowed": allowed, "reason": reason, "resource": req.resource}
    if ai_analysis:
        result["ai_analysis"] = ai_analysis
    return result
