"""
Mock ScoutAgent for Gatekeeper demo.
Usage: python mock_agent.py <session_id>
"""
import sys, time, requests

BASE = "http://localhost:8001"

def run(session_id: str):
    token = f"GK-{session_id}-TOKEN"
    resources = [
        ("network_config.json", "read"),
        ("server_inventory.csv", "read"),
        ("performance_logs.txt", "read"),
        ("employee_salaries.xlsx", "read"),
    ]
    print(f"\n[ScoutAgent] Starting scan — Session {session_id}\n")
    for resource, action in resources:
        resp = requests.post(f"{BASE}/access/request", json={
            "session_id": session_id, "token": token,
            "resource": resource, "action": action}).json()
        icon = "OK     " if resp["allowed"] else "BLOCKED"
        print(f"  [{icon}]  {resource}")
        time.sleep(1.2)
    print("\n[ScoutAgent] Scan complete. Requesting clean exit...\n")
    exit_resp = requests.post(f"{BASE}/session/exit",
        json={"session_id": session_id, "token": token}).json()
    print(f"Session closed.")
    print(f"Requests: {exit_resp['total_requests']} | Blocked: {exit_resp['blocked']}")
    print(f"Audit report: http://localhost:8001{exit_resp['pdf_url']}")

if __name__ == "__main__":
    session_id = sys.argv[1] if len(sys.argv) > 1 else input("Session ID: ")
    run(session_id)
