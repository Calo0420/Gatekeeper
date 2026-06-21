import os, hashlib, json
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors

os.makedirs("reports", exist_ok=True)

def generate_report(session: dict, logs: list) -> str:
    session_id = session["session_id"]
    path = f"reports/gatekeeper_{session_id}.pdf"
    doc = SimpleDocTemplate(path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    _logo = os.path.join(os.path.dirname(os.path.abspath(__file__)), "everforth_logo.png")
    if os.path.exists(_logo):
        _img = Image(_logo, width=200, height=200 * 180.0 / 1415.0)
        _img.hAlign = "LEFT"
        story.append(_img)
        story.append(Spacer(1, 10))

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

    # AI Risk Analysis section for blocked attempts
    blocked_with_ai = [l for l in logs if not l["allowed"] and l.get("ai_analysis")]
    if blocked_with_ai:
        story.append(Paragraph("AI Risk Analysis (Powered by AWS Bedrock):", styles["Heading3"]))
        for i, log in enumerate(blocked_with_ai, 1):
            analysis = log["ai_analysis"] if isinstance(log["ai_analysis"], dict) \
                else json.loads(log["ai_analysis"])
            risk_level = analysis.get("risk_level", "UNKNOWN")
            risk_color = {"LOW": "#2e7d32", "MEDIUM": "#f57f17",
                          "HIGH": "#d32f2f", "CRITICAL": "#b71c1c"}.get(risk_level, "#333333")
            story.append(Paragraph(
                f"<b>Incident {i}:</b> {log['resource']} ({log['action']})", styles["Normal"]))
            story.append(Paragraph(
                f"<font color='{risk_color}'><b>Risk Level: {risk_level}</b></font>", styles["Normal"]))
            story.append(Paragraph(f"<b>Explanation:</b> {analysis.get('risk_explanation', 'N/A')}", styles["Normal"]))
            story.append(Paragraph(f"<b>Threat:</b> {analysis.get('threat_assessment', 'N/A')}", styles["Normal"]))
            story.append(Paragraph(f"<b>Recommendation:</b> {analysis.get('recommendation', 'N/A')}", styles["Normal"]))
            story.append(Paragraph(
                f"<i>Model: {analysis.get('model_id', 'N/A')}</i>", styles["Normal"]))
            story.append(Spacer(1, 10))
        story.append(Spacer(1, 6))

    blocked = sum(1 for l in logs if not l["allowed"])
    story.append(Paragraph(f"Total: {len(logs)} requests | Blocked: {blocked}", styles["Normal"]))
    exit_status = "EXIT STATUS: CLEAN DISCONNECTION CONFIRMED" if blocked == 0 \
        else f"EXIT STATUS: {blocked} BLOCKED ATTEMPT(S) LOGGED"
    story.append(Paragraph(exit_status, styles["Heading3"]))
    story.append(Spacer(1, 12))

    # Tamper-evident audit hash over the FULL log content (see audit.py), not just
    # counts — altering what was accessed vs reported changes the hash.
    from audit import compute_hash
    audit_hash = compute_hash(session_id, logs)
    # Persist the issued hash as a sidecar so it can be independently re-verified later.
    try:
        with open(f"reports/gatekeeper_{session_id}.audit.json", "w") as _af:
            json.dump({"session_id": session_id, "audit_hash": audit_hash,
                       "count": len(logs), "blocked": blocked,
                       "issued_at": datetime.utcnow().isoformat() + "Z"}, _af)
    except Exception:
        pass
    story.append(Paragraph(f"Audit Hash (SHA-256): {audit_hash}", styles["Normal"]))
    story.append(Paragraph(f"Generated: {datetime.utcnow().isoformat()} UTC", styles["Normal"]))
    doc.build(story)
    return path
