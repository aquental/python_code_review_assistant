from fastapi import APIRouter, Request, HTTPException, Header, BackgroundTasks, Depends
from sqlalchemy.orm import Session
from database import get_session, Changeset, ChangesetFile
import hmac
import hashlib
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Dummy review engine for demonstration


class ReviewEngine:
    def review_full_changeset(self, db, changeset_id):
        return {"summary": "Review complete", "changeset_id": changeset_id}


review_engine = ReviewEngine()


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


@router.post("/webhook/github")
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_hub_signature_256: str = Header(None),
    db: Session = Depends(get_session)
):
    """Handle GitHub pull request webhooks"""
    payload = await request.body()

    # For demonstration, skip signature verification
    # if not verify_github_signature(payload, x_hub_signature_256, GITHUB_SECRET):
    #     raise HTTPException(status_code=401, detail="Invalid signature")

    try:
        event = json.loads(payload)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse webhook payload as JSON: {e}")
        db.rollback()
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    if event.get('action') not in ['opened', 'synchronize']:
        logger.info(f"Ignoring event with action: {event.get('action')}")
        return {"status": "ignored"}

    try:
        pr = event['pull_request']
        repo = event['repository']

        # Extract PR data
        pr_number = pr['number']
        title = pr['title']
        description = pr.get('body', '')
        author = pr['user']['login']
        repo_name = repo['full_name']

        logger.info(f"Processing PR #{pr_number}: {title} by {author}")

        # Create changeset object
        changeset = Changeset(
            title=title,
            description=description,
            author=author,
            status='pending'
        )

        # Add changeset to database session
        db.add(changeset)

        # Flush to get the changeset ID
        db.flush()

        # Fetch diff from GitHub API
        # For demonstration, we'll use a dummy diff
        diff_response = type('obj', (object,), {
            'status_code': 200,
            'text': "diff --git a/src/main.py b/src/main.py\n+print('hello')\ndiff --git a/src/utils.py b/src/utils.py\n+return True"
        })()

        if diff_response.status_code == 200:
            # Parse diff into individual files
            file_diffs = parse_pr_diff(diff_response.text)

            # Process each file in file_diffs
            for file_path, diff_content in file_diffs.items():
                changeset_file = ChangesetFile(
                    changeset_id=changeset.id,
                    file_path=file_path,
                    diff_content=diff_content
                )
                db.add(changeset_file)

            # Commit all changes
            db.commit()

            # Process review in background
            background_tasks.add_task(
                process_pr_review,
                changeset.id,
                pr_number,
                repo_name
            )

            logger.info(
                f"Successfully stored changeset {changeset.id} with {len(file_diffs)} files")
        else:
            logger.error(
                f"Failed to fetch diff, status code: {diff_response.status_code}")
            db.rollback()
            raise HTTPException(status_code=500, detail="Failed to fetch diff")

    except KeyError as e:
        logger.error(f"Missing required field in payload: {e}")
        db.rollback()
        raise HTTPException(
            status_code=400, detail=f"Missing required field: {e}")
    except Exception as e:
        logger.error(f"Unexpected error processing webhook: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")

    return {"status": "received"}


def parse_pr_diff(diff_text: str) -> dict:
    """Parse PR diff into file chunks"""
    files = {}
    current_file = None
    current_diff = []

    for line in diff_text.split('\n'):
        if line.startswith('diff --git'):
            if current_file and current_diff:
                files[current_file] = '\n'.join(current_diff)

            # Extract filename
            parts = line.split(' ')
            current_file = parts[3][2:] if len(parts) > 3 else 'unknown'
            current_diff = [line]
        elif current_file:
            current_diff.append(line)

    if current_file and current_diff:
        files[current_file] = '\n'.join(current_diff)

    return files


def process_pr_review(changeset_id: int, pr_number: int, repo_name: str):
    """Process review and post back to GitHub"""
    # Generate reviews
    db_gen = get_session()
    db = next(db_gen)
    try:
        reviews = review_engine.review_full_changeset(db, changeset_id)

        # Post comment to GitHub (requires GitHub token)
        # github_client = GitHubClient()
        # github_client.post_review_comment(repo_name, pr_number, reviews)
    finally:
        db.close()
