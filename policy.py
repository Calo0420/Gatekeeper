"""
policy.py
Gatekeeper — Data Classification Policy

Enforces enterprise data-protection controls on AI agent access requests.

Standard alignment:
  - CIS Controls v8 - Control 3: Data Protection
  - NIST SP 800-53 - AC-3: Access Enforcement (least privilege)

Policy statement:
  AI agents may DETECT the existence of credential files but may NOT READ
  their contents. Detection is permitted; content access is blocked.
"""

import os
from urllib.parse import unquote

# Credential / secret resources - classified CONFIDENTIAL. A read-only
# assessment agent has no legitimate business reason to read these.
RESTRICTED_EXTENSIONS = (
    ".env", ".pem", ".key", ".pfx", ".p12", ".keystore", ".jks", ".ppk",
)
RESTRICTED_NAME_HINTS = (
    "credential", "secret", "id_rsa", "id_ed25519", "private_key",
    "privatekey", "api_key", "apikey", ".aws/credentials",
    ".git-credentials", "htpasswd", "shadow",
)

# Actions that READ contents - blocked on restricted resources.
CONTENT_READ_ACTIONS = (
    "read", "read_contents", "cat", "get", "get_contents", "download",
    "fetch", "open", "view", "dump", "copy", "exfiltrate", "print",
)

# Actions that only DETECT existence / metadata - always permitted.
DETECTION_ACTIONS = (
    "detect", "exists", "stat", "list", "ls", "scan", "flag",
    "enumerate", "discover", "execute",
)

FRAMEWORKS = [
    "CIS Control 3 - Data Protection",
    "NIST 800-53 AC-3 - Access Enforcement (least privilege)",
]

CLASSIFICATION = "CONFIDENTIAL - Credential / Secret"
RESTRICTED_TYPES_DISPLAY = ".env, .pem, .key"


def _normalize(resource: str) -> str:
    """
    Canonicalize a resource path before policy evaluation.
    - URL-decode percent-encoded characters (catches %00, %2e, etc.)
    - Strip null bytes and surrounding whitespace
    - Resolve . and .. components (os.path.normpath)
    - Lowercase for case-insensitive comparison
    """
    if not resource:
        return ""
    # URL-decode (handles %00 null bytes, %2e dot encoding, etc.)
    r = unquote(resource)
    # Strip null bytes and whitespace
    r = r.replace("\x00", "").strip()
    # Resolve . and .. path components
    r = os.path.normpath(r)
    # Resolve symlinks for paths that exist locally on this host.
    # Prevents bypass via: ln -s /opt/Gatekeeper/.env /tmp/notenv.txt
    # os.path.islink() catches dangling symlinks too.
    if os.path.islink(r) or os.path.exists(r):
        r = os.path.realpath(r)
    # Lowercase for case-insensitive matching
    return r.lower()


def _has_restricted_extension(r: str) -> bool:
    """
    Check if any component of the filename contains a restricted extension.
    Catches: .env, .env.bak, .env.swp, .env~, .env., app.key.bak, etc.
    """
    filename = os.path.basename(r)
    # Direct suffix match
    if filename.endswith(RESTRICTED_EXTENSIONS):
        return True
    # Check if any restricted extension appears anywhere in the filename
    # (catches .env.bak, .env.swp, .env~, .env.)
    for ext in RESTRICTED_EXTENSIONS:
        if ext in filename:
            return True
    return False


def is_credential_resource(resource: str) -> bool:
    """True if the resource is a credential/secret file per data classification."""
    r = _normalize(resource)
    if _has_restricted_extension(r):
        return True
    return any(hint in r for hint in RESTRICTED_NAME_HINTS)


def is_content_read(action: str) -> bool:
    """True if the action reads file contents (vs. only detecting existence)."""
    return (action or "").lower().strip() in CONTENT_READ_ACTIONS


def classify(resource: str, action: str) -> dict:
    """
    Apply the data classification policy to an access request.

    decision:
      "block" -> restricted credential content-read; deny outright
      "pass"  -> no policy violation; defer to least-privilege scope check
    """
    credential = is_credential_resource(resource)
    content_read = is_content_read(action)

    if credential and content_read:
        return {
            "decision": "block",
            "control": "data_classification",
            "classification": CLASSIFICATION,
            "frameworks": FRAMEWORKS,
            "reason": (
                "DATA CLASSIFICATION POLICY: %s is classified %s. AI agents "
                "may detect that this file exists but may not read its contents. "
                "Content access BLOCKED per CIS Control 3 (Data Protection) and "
                "NIST 800-53 AC-3 (Access Enforcement, least privilege)."
                % (resource, CLASSIFICATION)
            ),
        }

    return {
        "decision": "pass",
        "control": "least_privilege",
        "credential": credential,
        "frameworks": FRAMEWORKS if credential else [],
    }
