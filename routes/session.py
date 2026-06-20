import uuid, json, os
from datetime import datetime
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import FileResponse, JSONResponse
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

@router.get("/{session_id}/status")
def session_status(session_id: str):
    """ScoutAgent polls this to check if its session has been approved."""
    db = get_db()
    s = db.execute("SELECT session_id, status, approved_scope FROM sessions WHERE session_id=?",
                   (session_id,)).fetchone()
    db.close()
    if not s:
        raise HTTPException(404, "Session not found")
    result = {"session_id": s["session_id"], "status": s["status"]}
    if s["status"] == "active":
        result["token"] = f"GK-{session_id}-TOKEN"
        result["approved_scope"] = json.loads(s["approved_scope"] or "[]")
    return result

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


@router.get("/list")
def list_sessions():
    """Recent Gatekeeper sessions (newest first) for the live UI."""
    db = get_db()
    rows = db.execute(
        "SELECT session_id, agent_name, agent_id, status, started_at, "
        "exited_at, approved_by FROM sessions ORDER BY started_at DESC LIMIT 25"
    ).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        counts = db.execute(
            "SELECT COUNT(*) c, COALESCE(SUM(1-allowed),0) blocked "
            "FROM access_logs WHERE session_id=?", (d["session_id"],)
        ).fetchone()
        d["total_requests"] = counts["c"]
        d["blocked"] = counts["blocked"]
        out.append(d)
    db.close()
    return JSONResponse(out)


@router.get("/{session_id}/detail")
def session_detail(session_id: str):
    """Full session record + real access logs for the live UI."""
    db = get_db()
    s = db.execute("SELECT * FROM sessions WHERE session_id=?",
                   (session_id,)).fetchone()
    if not s:
        db.close()
        raise HTTPException(404, "Session not found")
    logs = db.execute(
        "SELECT resource, action, allowed, reason, ai_analysis, timestamp "
        "FROM access_logs WHERE session_id=? ORDER BY timestamp", (session_id,)
    ).fetchall()
    db.close()

    out = dict(s)
    out["requested_scope"] = json.loads(out.get("requested_scope") or "[]")
    out["approved_scope"] = json.loads(out.get("approved_scope") or "[]")

    log_list = []
    for l in logs:
        d = dict(l)
        if d.get("ai_analysis"):
            try:
                d["ai_analysis"] = json.loads(d["ai_analysis"])
            except Exception:
                pass
        log_list.append(d)
    out["access_logs"] = log_list
    out["allowed_count"] = sum(1 for l in log_list if l["allowed"])
    out["blocked_count"] = sum(1 for l in log_list if not l["allowed"])
    return JSONResponse(out)
