import os, hashlib, json
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors

os.makedirs("reports", exist_ok=True)

def generate_report(session: dict, logs: list) -> str:
    session_id = session["session_id"]
    path = f"reports/gatekeeper_{session_id}.pdf"
    doc = SimpleDocTemplate(path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("GATEKEEPER — AI TRUST AUDIT REPORT", styles["Title"]))
    story.append(Paragraph("Everforth Innovation Labs | Rogue Protocol", styles["Normal"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Session ID: {session_id}", styles["Heading2"]))
    story.append(Paragraph(f"Agent: {session['agent_name']} ({session['agent_id']})", styles["Normal"]))
    story.append(Paragraph(f"Approved by: {session['approved_by']}", styles["Normal"]))
    story.append(Paragraph(f"Start: {session['started_at']}", styles["Normal"]))
    story.append(Paragraph(f"Exit: {session['exited_at']}", styles["Normal"]))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Approved Scope:", styles["Heading3"]))
    for item in json.loads(session["approved_scope"]):
        story.append(Paragraph(f"  - {item}", styles["Normal"]))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Access Log:", styles["Heading3"]))
    table_data = [["Timestamp", "Resource", "Action", "Status"]]
    for log in logs:
        table_data.append([log["timestamp"][:19], log["resource"],
                           log["action"], "ALLOWED" if log["allowed"] else "BLOCKED"])
    table = Table(table_data, colWidths=[140, 160, 80, 100])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#1a2e3c")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#f5f5f5")]),
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
    ]))
    story.append(table)
    story.append(Spacer(1, 16))

    blocked = sum(1 for l in logs if not l["allowed"])
    story.append(Paragraph(f"Total: {len(logs)} requests | Blocked: {blocked}", styles["Normal"]))
    exit_status = "EXIT STATUS: CLEAN DISCONNECTION CONFIRMED" if blocked == 0 \
        else f"EXIT STATUS: {blocked} BLOCKED ATTEMPT(S) LOGGED"
    story.append(Paragraph(exit_status, styles["Heading3"]))
    story.append(Spacer(1, 12))

    audit_hash = hashlib.sha256(
        json.dumps({"session": session_id, "logs": len(logs), "blocked": blocked}).encode()
    ).hexdigest()
    story.append(Paragraph(f"Audit Hash (SHA-256): {audit_hash}", styles["Normal"]))
    story.append(Paragraph(f"Generated: {datetime.utcnow().isoformat()} UTC", styles["Normal"]))
    doc.build(story)
    return path
