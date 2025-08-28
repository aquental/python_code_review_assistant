from fastapi import APIRouter, Request, HTTPException, Header, BackgroundTasks, Depends
from sqlalchemy.orm import Session
import hmac
import hashlib
import json
import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()


def parse_pr_diff(diff_text: str) -> dict:
    """Parse PR diff into file chunks, handling GitHub's diff format including renames and binary files."""
    files = {}
    current_file = None
    current_diff = []

    # Regex patterns for GitHub diff format
    diff_pattern = re.compile(
        r'^diff --git a/(.+?) b/(.+?)(?:\s|$)', re.MULTILINE)
    binary_pattern = re.compile(r'Binary files a/(.+?) and b/(.+?) differ')

    # Split diff into lines and process
    lines = diff_text.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]

        # Handle diff header
        diff_match = diff_pattern.match(line)
        if diff_match:
            if current_file and current_diff:
                files[current_file] = '\n'.join(current_diff)

            old_path, new_path = diff_match.groups()
            # Use new_path for renamed files; fallback to old_path if new_path is /dev/null (deleted file)
            current_file = new_path if new_path != '/dev/null' else old_path
            current_diff = [line]
            i += 1
            continue

        # Handle binary files
        binary_match = binary_pattern.match(line)
        if binary_match:
            if current_file and current_diff:
                files[current_file] = '\n'.join(current_diff)

            old_path, new_path = binary_match.groups()
            current_file = new_path if new_path != '/dev/null' else old_path
            current_diff = [line, 'Binary file']
            files[current_file] = '\n'.join(current_diff)
            current_file = None
            current_diff = []
            i += 1
            continue

        # Collect diff content
        if current_file:
            current_diff.append(line)

        i += 1

    # Store final file diff
    if current_file and current_diff:
        files[current_file] = '\n'.join(current_diff)

    return files


def process_pr_review(changeset_id: int, pr_number: int, repo_name: str):
    """Process review and post back to GitHub."""
    logger.info(
        f"Starting background review for changeset {changeset_id}, PR #{pr_number}")

    db = get_session()
    try:
        # Update changeset status to in_progress
        changeset = next((obj for obj in db.objects if isinstance(
            obj, Changeset) and obj.id == changeset_id), None)
        if changeset:
            changeset.status = 'in_progress'
            db.commit()
            logger.info(f"Updated changeset {changeset_id} to in_progress")

        # Generate reviews
        reviews = review_engine.review_full_changeset(db, changeset_id)

        # Post comment to GitHub (mocked for demonstration)
        # github_client = GitHubClient()
        # github_client.post_review_comment(repo_name, pr_number, reviews)

        # Update changeset status to completed
        if changeset:
            changeset.status = 'completed'
            db.commit()
            logger.info(
                f"Completed review for changeset {changeset_id}, PR #{pr_number}")

    except Exception as e:
        logger.error(
            f"Error processing review for changeset {changeset_id}: {str(e)}")
        if changeset:
            changeset.status = 'failed'
            db.commit()
    finally:
        db.close()

# Dummy implementations for demonstration purposes


def get_session():
    class DummySession:
        def __init__(self):
            self.objects = []
            self._id_counter = 1

        def add(self, obj):
            self.objects.append(obj)
            logger.info(f"Added {type(obj).__name__} to session")

        def flush(self):
            for obj in self.objects:
                if isinstance(obj, Changeset) and obj.id is None:
                    obj.id = self._id_counter
                    self._id_counter += 1
                    logger.info(f"Assigned ID {obj.id} to changeset")

        def commit(self):
            logger.info(f"Committed {len(self.objects)} objects to database")

        def close(self):
            logger.info("Closed database session")

    return DummySession()


class Changeset:
    def __init__(self, title, description, author, status='pending'):
        self.title = title
        self.description = description
        self.author = author
        self.status = status
        self.id = None


class ChangesetFile:
    def __init__(self, changeset_id, file_path, diff_content):
        self.changeset_id = changeset_id
        self.file_path = file_path
        self.diff_content = diff_content


class ReviewEngine:
    def review_full_changeset(self, db, changeset_id):
        return {"summary": "Review complete", "changeset_id": changeset_id}


review_engine = ReviewEngine()


def verify_github_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify GitHub webhook signature."""
    if not signature or not signature.startswith('sha256='):
        return False

    expected = 'sha256=' + hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected, signature)


@router.post("/webhook/github")
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_hub_signature_256: str = Header(None),
    db: Session = Depends(get_session)
):
    """Handle GitHub pull request webhooks."""
    payload = await request.body()

    # For demonstration, skip signature verification
    # if not verify_github_signature(payload, x_hub_signature_256, GITHUB_SECRET):
    #     raise HTTPException(status_code=401, detail="Invalid signature")

    event = json.loads(payload)

    if event.get('action') in ['opened', 'synchronize']:
        pr = event['pull_request']
        logger.info(
            f"Received PR #{pr['number']} {pr['title']} ({event['action']})")

        # Create changeset from PR
        changeset = Changeset(
            title=pr['title'],
            description=pr.get('body', ''),
            author=pr['user']['login'],
            status='pending'
        )
        db.add(changeset)
        db.flush()

        # Mock diff response for testing
        diff_response = type('obj', (object,), {
            'status_code': 200,
            'text': """diff --git a/src/old_file.py b/src/new_file.py
index 1234567..89abcde 100644
--- a/src/old_file.py
+++ b/src/new_file.py
@@ -1 +1 @@
-print('hello')
+print('world')
diff --git a/docs/readme.md b/docs/readme.md
index abcdef1..2345678 100644
--- a/docs/readme.md
+++ b/docs/readme.md
@@ -1 +1,2 @@
 # Project
+# Updated
Binary files a/image.png b/image.png differ"""
        })()

        if diff_response.status_code == 200:
            file_diffs = parse_pr_diff(diff_response.text)

            for file_path, diff_content in file_diffs.items():
                changeset_file = ChangesetFile(
                    changeset_id=changeset.id,
                    file_path=file_path,
                    diff_content=diff_content
                )
                db.add(changeset_file)

            # Update status to pending before scheduling
            changeset.status = 'pending'
            db.commit()
            logger.info(
                f"Scheduled review for changeset {changeset.id}, PR #{pr['number']}")

            # Schedule background review
            background_tasks.add_task(
                process_pr_review,
                changeset_id=changeset.id,
                pr_number=pr['number'],
                repo_name=event['repository']['full_name']
            )

    return {"status": "received"}
