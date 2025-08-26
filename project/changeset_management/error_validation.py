from fastapi import FastAPI, HTTPException, Request, status, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging
from typing import Union, List, Optional
from pydantic import BaseModel, field_validator
import re

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()


class UserRequest(BaseModel):
    name: str
    author: str

    @field_validator('author')
    @classmethod
    def validate_author_email(cls, v):
        """Validate email format using regex pattern"""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v.strip()):
            raise ValueError('Invalid email format')
        return v.strip()


class CodeReviewException(Exception):
    """Custom exception for code review operations"""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


@app.exception_handler(CodeReviewException)
async def code_review_exception_handler(request: Request, exc: CodeReviewException):
    logger.error(f"Code review error: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message, "type": "code_review_error"}
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": "Invalid input data", "details": exc.errors()}
    )


class FileChangeRequest(BaseModel):
    file_path: str
    diff_content: str

    @field_validator('file_path')
    @classmethod
    def validate_file_path(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('File path cannot be empty')

        # Basic security check - no parent directory access
        if '..' in v or v.startswith('/'):
            raise ValueError('Invalid file path')

        return v.strip()

    @field_validator('diff_content')
    @classmethod
    def validate_diff_content(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Diff content cannot be empty')

        if len(v) > 50000:  # 50KB limit
            raise ValueError('Diff content too large')

        return v


class ChangesetRequest(BaseModel):
    title: str
    description: Optional[str] = None
    author: str
    files: List[FileChangeRequest]

    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Title cannot be empty')

        if len(v) > 200:
            raise ValueError('Title too long (max 200 characters)')

        return v.strip()

    @field_validator('author')
    @classmethod
    def validate_author(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Author cannot be empty')

        # Basic email or username validation
        if not re.match(r'^[a-zA-Z0-9._-]+(@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})?$', v):
            raise ValueError('Invalid author format')

        return v.strip()

    @field_validator('files')
    @classmethod
    def validate_files(cls, v):
        if not v or len(v) == 0:
            raise ValueError('At least one file must be provided')

        if len(v) > 20:  # Limit to 20 files per changeset
            raise ValueError('Too many files (max 20)')

        return v


@app.post("/api/users", response_model=dict)
def create_user(request: UserRequest):
    """Create a new user with validation"""
    return {"message": "User created successfully", "name": request.name, "email": request.author}


@app.post("/api/changesets", response_model=dict)
def submit_changeset(request: ChangesetRequest, background_tasks: BackgroundTasks):
    """Submit a new changeset for review with validation"""
    try:
        # Simulate changeset creation without database
        changeset_id = 1
        logger.info(f"Changeset {changeset_id} created by {request.author}")

        return {"message": "Changeset submitted", "changeset_id": changeset_id}

    except Exception as e:
        logger.error(f"Failed to create changeset: {str(e)}")
        raise CodeReviewException("Failed to create changeset", 500)


# Test the validation
if __name__ == "__main__":
    # Test valid email
    try:
        user = UserRequest(name="John Doe", author="john.doe@example.com")
        print(f"✓ Valid email: {user.author}")
    except Exception as e:
        print(f"✗ Error: {e}")

    # Test invalid email
    try:
        user = UserRequest(name="Jane Doe", author="invalid-email")
        print(f"✓ Should not reach here: {user.author}")
    except Exception as e:
        print(f"✓ Correctly caught invalid email: {e}")

    print("Email validation test completed!")
