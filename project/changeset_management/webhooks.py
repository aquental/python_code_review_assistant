from fastapi import APIRouter, Request
import json
import hmac
import hashlib
import re

router = APIRouter()

class Changeset:
    def __init__(self, title, description, author, status='pending'):
        self.title = title
        self.description = description
        self.author = author
        self.status = status
        self.id = 1  # Dummy ID for testing

def get_session():
    """Return a dummy session for testing"""
    class DummySession:
        def add(self, obj): pass
        def flush(self): pass
        def commit(self): pass
        def close(self): pass
    return DummySession()

def verify_github_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify GitHub webhook signature"""
    if not signature or not signature.startswith('sha256='):
        return False

    expected = 'sha256=' + hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected, signature)

def parse_pr_diff(diff_content: str) -> dict:
    """Parse PR diff content and extract file changes"""
    files = {}
    current_file = None
    
    for line in diff_content.split('\n'):
        if line.startswith('diff --git'):
            # Extract file path from diff header
            match = re.search(r'diff --git a/(.*?) b/(.*?)$', line)
            if match:
                current_file = match.group(1)
                files[current_file] = []
        elif current_file and (line.startswith('+') or line.startswith('-')):
            files[current_file].append(line)
    
    return files

def process_pr_review(changeset_id: int, pr_number: int, repo_name: str):
    """Process PR review in background"""
    print(f"Processing review for changeset {changeset_id}, PR {pr_number} in {repo_name}")

@router.post("/webhook/github")
async def github_webhook(request: Request):
    """Handle GitHub pull request webhooks"""
    # Read the request body as bytes
    payload_bytes = await request.body()
    
    # Parse the payload as JSON
    try:
        payload = json.loads(payload_bytes)
    except json.JSONDecodeError:
        return {"message": "Invalid JSON payload"}
    
    # Check if the action is 'opened' or 'synchronize'
    action = payload.get('action')
    if action in ['opened', 'synchronize']:
        return {"message": "PR event received"}
    
    # Return for other actions
    return {"message": "Event ignored"}
