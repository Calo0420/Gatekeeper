import uuid, json, os
from datetime import datetime
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from db import get_db
from report_generator import generate_report

router = APIRouter()
templates = Jinja2Templates(directory="templates")

class StartRequest(BaseModel):
    agent_id: str
    agent_name: str
    requested_scope: list[str]

class ApproveRequest(BaseModel):
    session_id: str
    approved_by: str
    approved_scope: list[str]

class ExitRequest(BaseModel):
    session_id: str
    token: str

@router.post("/start")
def start_session(req: StartRequest):
    session_id = str(uuid.uuid4())[:8].upper()
    db = get_db()
    db.execute("""INSERT INTO sessions
        (session_id, agent_id, agent_name, requested_scope, status, started_at)
        VALUES (?, ?, ?, ?, 'pending', ?)""",
        (session_id, req.agent_id, req.agent_name,
         json.dumps(req.requested_scope), datetime.utcnow().isoformat()))
    db.commit()
    db.close()
    return {"session_id": session_id, "status": "pending_approval"}

@router.post("/approve")
def approve_session(req: ApproveRequest):
    db = get_db()
    db.execute("UPDATE sessions SET status='active', approved_by=?, approved_scope=? WHERE session_id=?",
        (req.approved_by, json.dumps(req.approved_scope), req.session_id))
    db.commit()
    db.close()
    return {"session_id": req.session_id, "status": "active",
            "token": f"GK-{req.session_id}-TOKEN"}

@router.post("/exit")
def exit_session(req: ExitRequest):
    db = get_db()
    db.execute("UPDATE sessions SET status='closed', exited_at=? WHERE session_id=?",
        (datetime.utcnow().isoformat(), req.session_id))
    db.commit()
    session = db.execute("SELECT * FROM sessions WHERE session_id=?",
                         (req.session_id,)).fetchone()
    logs = db.execute("SELECT * FROM access_logs WHERE session_id=?",
                      (req.session_id,)).fetchall()
    db.close()
    pdf_path = generate_report(dict(session), [dict(l) for l in logs])
    blocked = sum(1 for l in logs if not l["allowed"])
    return {"session_id": req.session_id, "status": "closed",
            "pdf_url": f"/session/{req.session_id}/report",
            "total_requests": len(logs), "blocked": blocked}

@router.get("/{session_id}/report")
def download_report(session_id: str):
    path = f"reports/gatekeeper_{session_id}.pdf"
    if not os.path.exists(path):
        raise HTTPException(404, "Report not found")
    return FileResponse(path, media_type="application/pdf",
                        filename=f"gatekeeper_audit_{session_id}.pdf")

@router.get("/approve-ui/{session_id}")
def approval_ui(request: Request, session_id: str):
    db = get_db()
    s = db.execute("SELECT * FROM sessions WHERE session_id=?",
                   (session_id,)).fetchone()
    db.close()
    return templates.TemplateResponse("approval.html", {
        "request": request, "session": dict(s),
        "scope": json.loads(s["requested_scope"])})
