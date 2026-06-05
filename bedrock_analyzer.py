"""
bedrock_analyzer.py
Gatekeeper — AI Trust Gateway
Uses AWS Bedrock (Claude Sonnet 4.6) to analyze blocked access attempts
and generate risk explanations for audit reports.
"""

import json
import boto3
from botocore.exceptions import ClientError

MODEL_ID = "us.anthropic.claude-sonnet-4-6"
REGION = "us-east-2"
AWS_PROFILE = "390346501482_Architect-PowerUser-Guarded"


def get_bedrock_client():
    session = boto3.Session(profile_name=AWS_PROFILE)
    return session.client("bedrock-runtime", region_name=REGION)


def analyze_blocked_attempt(
    agent_name: str,
    agent_id: str,
    resource: str,
    action: str,
    approved_scope: list,
    session_id: str
) -> dict:
    """
    Calls Claude Sonnet 4.6 via Bedrock to analyze a blocked access attempt.
    Returns a risk analysis dict with explanation and severity.
    """
    prompt = f"""You are a security analyst reviewing an AI agent access violation.

INCIDENT DETAILS:
- Session ID: {session_id}
- Agent: {agent_name} ({agent_id})
- Blocked Resource: {resource}
- Action Attempted: {action}
- Approved Scope: {', '.join(approved_scope)}

The agent attempted to access a resource OUTSIDE its approved scope.

Provide a concise security analysis in JSON format with these exact fields:
{{
  "risk_level": "LOW | MEDIUM | HIGH | CRITICAL",
  "risk_explanation": "One sentence explaining why this access was blocked",
  "threat_assessment": "One sentence describing what could happen if this access was granted",
  "recommendation": "One sentence recommending a specific action"
}}

Be specific and technical. Reference the actual resource name and agent in your response.
Return ONLY the JSON object, no other text."""

    try:
        client = get_bedrock_client()
        response = client.invoke_model(
            modelId=MODEL_ID,
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 400,
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            }),
            contentType="application/json",
            accept="application/json"
        )

        body = json.loads(response["body"].read())
        text = body["content"][0]["text"].strip()

        # Clean up if model wraps in markdown
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        text = text.strip()

        analysis = json.loads(text)
        analysis["powered_by"] = "AWS Bedrock — Claude Sonnet 4.6"
        analysis["model_id"] = MODEL_ID
        return analysis

    except ClientError as e:
        return {
            "risk_level": "HIGH",
            "risk_explanation": f"Access to {resource} was blocked — outside approved scope.",
            "threat_assessment": "Unauthorized access could expose sensitive data.",
            "recommendation": "Review agent permissions and resubmit with correct scope.",
            "powered_by": "Gatekeeper (Bedrock unavailable)",
            "error": str(e)
        }
    except Exception as e:
        return {
            "risk_level": "HIGH",
            "risk_explanation": f"Access to {resource} was blocked — outside approved scope.",
            "threat_assessment": "Unauthorized access could expose sensitive data.",
            "recommendation": "Review agent permissions and resubmit with correct scope.",
            "powered_by": "Gatekeeper (Bedrock unavailable)",
            "error": str(e)
        }


if __name__ == "__main__":
    # Quick test
    print("Testing Bedrock analyzer...")
    result = analyze_blocked_attempt(
        agent_name="ScoutAgent",
        agent_id="scout-001",
        resource="employee_salaries.xlsx",
        action="read",
        approved_scope=["network_config.json", "server_inventory.csv", "performance_logs.txt"],
        session_id="TEST-001"
    )
    print(json.dumps(result, indent=2))
