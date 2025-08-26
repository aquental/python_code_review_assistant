from fastapi import FastAPI, HTTPException, Request, status, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker, declarative_base
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
import logging
from typing import Union, List, Optional
from pydantic import BaseModel, field_validator
import re
from datetime import datetime

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
    # Convert errors to JSON-serializable format
    serializable_errors = []
    for error in exc.errors():
        serializable_error = {
            "type": error.get("type"),
            "loc": error.get("loc"),
            "msg": error.get("msg"),
            "input": str(error.get("input"))
        }
        serializable_errors.append(serializable_error)
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": "Invalid input data", "details": serializable_errors}
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
    """Submit a new changeset for review with proper database error handling"""
    try:
        # Create changeset
        changeset = Changeset(
            title=request.title,
            description=request.description,
            author=request.author
        )
        db.add(changeset)
        db.flush()  # Get the changeset ID before adding files
        
        # Add files
        for file_req in request.files:
            changeset_file = ChangesetFile(
                changeset_id=changeset.id,
                file_path=file_req.file_path,
                diff_content=file_req.diff_content
            )
            db.add(changeset_file)
        
        # Commit all changes
        db.commit()
        
        logger.info(f"Changeset {changeset.id} created by {request.author}")
        
        # Process review in background
        background_tasks.add_task(process_changeset_review, changeset.id)
        
        return {"message": "Changeset submitted", "changeset_id": changeset.id}
    
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Database integrity error: {str(e)}")
        raise CodeReviewException(
            message="Database constraint violation - duplicate data or invalid foreign key",
            status_code=409
        )
    
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error creating changeset: {str(e)}")
        raise CodeReviewException(
            message="Failed to create changeset",
            status_code=500
            )

if __name__ == "__main__":
    from fastapi.testclient import TestClient
    
    # Create test client
    client = TestClient(app)
    
    print("Testing database error handling...")
    
    # Test case 1: Valid changeset creation
    print("\n1. Testing valid changeset creation:")
    response = client.post("/api/changesets", json={
        "title": "Add new feature",
        "author": "developer@example.com",
        "files": [
            {
                "file_path": "src/main.py",
                "diff_content": "@@ -1,5 +1,7 @@\n+def new_function():\n+    return True"
            }
        ]
    })
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test case 2: Invalid input (should trigger validation error)
    print("\n2. Testing invalid input:")
    response = client.post("/api/changesets", json={
        "title": "",  # Empty title should fail validation
        "author": "developer@example.com",
        "files": []
    })
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test case 3: Invalid file path
    print("\n3. Testing invalid file path:")
    response = client.post("/api/changesets", json={
        "title": "Test changeset",
        "author": "developer@example.com",
        "files": [
            {
                "file_path": "../../../etc/passwd",  # Should fail validation
                "diff_content": "malicious content"
            }
        ]
    })
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    print("\n✅ Database error handling testing completed!")
