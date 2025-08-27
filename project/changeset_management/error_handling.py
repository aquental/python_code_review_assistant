from fastapi import FastAPI, HTTPException, Request, status, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime
import logging
from typing import Union, List, Optional
from pydantic import BaseModel, field_validator
import re
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Database setup
DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database models


class Changeset(Base):
    __tablename__ = "changesets"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200))
    description = Column(Text, nullable=True)
    author = Column(String(100))
    status = Column(String(20), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)


class ChangesetFile(Base):
    __tablename__ = "changeset_files"
    id = Column(Integer, primary_key=True, index=True)
    changeset_id = Column(Integer, ForeignKey("changesets.id"))
    file_path = Column(String(255))
    diff_content = Column(Text)


# Create database tables
Base.metadata.create_all(bind=engine)


def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class FileChangeRequest(BaseModel):
    file_path: str
    diff_content: str

    @field_validator('file_path')
    def validate_file_path(cls, v):
        if not v or v.isspace():
            raise ValueError('File path cannot be empty')

        # Prevent directory traversal
        if '..' in v or v.startswith('/') or v.startswith('\\'):
            raise ValueError('Invalid file path: Directory traversal detected')

        # Normalize path and check again
        normalized_path = os.path.normpath(v)
        if '..' in normalized_path or normalized_path.startswith(os.sep):
            raise ValueError('Invalid file path: Directory traversal detected')

        return v

    @field_validator('diff_content')
    def validate_diff_content(cls, v):
        if not v or v.isspace():
            raise ValueError('Diff content cannot be empty')

        # Enforce 50KB size limit (50 * 1024 bytes)
        max_size = 50 * 1024
        if len(v.encode('utf-8')) > max_size:
            raise ValueError(
                f'Diff content exceeds {max_size/1024}KB size limit')

        return v


class ChangesetRequest(BaseModel):
    title: str
    description: Optional[str] = None
    author: str
    files: List[FileChangeRequest]

    @field_validator('title')
    def validate_title(cls, v):
        if not v or v.isspace():
            raise ValueError('Title cannot be empty')
        if len(v) > 200:
            raise ValueError('Title cannot exceed 200 characters')
        return v

    @field_validator('author')
    def validate_author(cls, v):
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, v):
            raise ValueError('Invalid email format')
        return v


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

    cleaned_errors = []
    for error in exc.errors():
        cleaned_error = {
            "type": error.get("type"),
            "loc": error.get("loc"),
            "msg": error.get("msg"),
            "input": str(error.get("input", ""))[:100] + "..." if len(str(error.get("input", ""))) > 100 else str(error.get("input", ""))
        }
        cleaned_errors.append(cleaned_error)

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": "Invalid input data", "details": cleaned_errors}
    )


@app.exception_handler(IntegrityError)
async def database_exception_handler(request: Request, exc: IntegrityError):
    logger.error(f"Database error: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"error": "Database constraint violation"}
    )


def process_changeset_review(changeset_id: int):
    pass


@app.post("/api/changesets", response_model=dict)
def submit_changeset(
    request: ChangesetRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_session)
):
    """Submit a new changeset for review with validation"""
    try:
        # Create changeset
        changeset = Changeset(
            title=request.title,
            description=request.description,
            author=request.author
        )
        db.add(changeset)
        db.flush()

        # Add files
        for file_req in request.files:
            changeset_file = ChangesetFile(
                changeset_id=changeset.id,
                file_path=file_req.file_path,
                diff_content=file_req.diff_content
            )
            db.add(changeset_file)

        db.commit()
        logger.info(f"Changeset {changeset.id} created by {request.author}")

        # Process review in background
        background_tasks.add_task(process_changeset_review, changeset.id)

        return {"message": "Changeset submitted", "changeset_id": changeset.id}

    except IntegrityError:
        db.rollback()
        raise CodeReviewException(
            message="Database constraint violation",
            status_code=status.HTTP_409_CONFLICT
        )

    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error: {str(e)}")
        raise CodeReviewException(
            message="Failed to create changeset",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


if __name__ == "__main__":
    from fastapi.testclient import TestClient

    # Create test client
    client = TestClient(app)

    print("Testing comprehensive changeset validation and error handling...")

    # Test case 1: Valid changeset submission
    print("\n1. Testing valid changeset:")
    valid_changeset = {
        "title": "Fix authentication bug",
        "description": "Updated login validation logic",
        "author": "developer@example.com",
        "files": [
            {
                "file_path": "src/auth.py",
                "diff_content": "- old_code\n+ new_code"
            }
        ]
    }
    response = client.post("/api/changesets", json=valid_changeset)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

    # Test case 2: Invalid title (too long)
    print("\n2. Testing title too long:")
    long_title_changeset = {
        "title": "A" * 250,  # Exceeds 200 character limit
        "author": "developer@example.com",
        "files": [{"file_path": "test.py", "diff_content": "test"}]
    }
    response = client.post("/api/changesets", json=long_title_changeset)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

    # Test case 3: Invalid email format
    print("\n3. Testing invalid email:")
    invalid_email_changeset = {
        "title": "Test changeset",
        "author": "not-an-email",
        "files": [{"file_path": "test.py", "diff_content": "test"}]
    }
    response = client.post("/api/changesets", json=invalid_email_changeset)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

    # Test case 4: Invalid file path (directory traversal)
    print("\n4. Testing directory traversal attack:")
    traversal_changeset = {
        "title": "Test changeset",
        "author": "developer@example.com",
        "files": [{"file_path": "../../../etc/passwd", "diff_content": "malicious"}]
    }
    response = client.post("/api/changesets", json=traversal_changeset)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

    # Test case 5: Content too large
    print("\n5. Testing content size limit:")
    large_content_changeset = {
        "title": "Test changeset",
        "author": "developer@example.com",
        # Exceeds 50KB
        "files": [{"file_path": "test.py", "diff_content": "x" * 60000}]
    }
    response = client.post("/api/changesets", json=large_content_changeset)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

    print("\n✅ Comprehensive validation and error handling testing completed!")
