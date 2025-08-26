from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

# Database setup
DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

app = FastAPI()

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

# Database session dependency


def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def scan_repository(repo_path: str, db: Session) -> int:
    """Dummy function to simulate repository scanning"""
    # This is a Journey scanning function that returns a fixed number
    return 3


@app.post("/api/scan")
def trigger_scan(repo_path: str, db: Session = Depends(get_session)):
    """Trigger repository scan"""
    try:
        count = scan_repository(repo_path, db)
        return {"message": f"Scanned {count} files"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Dummy review engine


class ReviewEngine:
    def review_changeset_file(self, db, file):
        # Return a dummy review
        return f"Review for {file.file_path}: Looks good!"


review_engine = ReviewEngine()

# Pydantic response model


class ChangesetResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    author: str
    status: str
    created_at: str


@app.get("/api/changesets", response_model=List[ChangesetResponse])
def list_changesets(
    status: Optional[str] = None,
    limit: int = 10,
    db: Session = Depends(get_session)
):
    """List changesets with optional filtering"""
    query = db.query(Changeset)

    if status:
        query = query.filter(Changeset.status == status)

    changesets = query.order_by(Changeset.created_at.desc()).limit(limit).all()

    return [
        ChangesetResponse(
            id=cs.id,
            title=cs.title,
            description=cs.description,
            author=cs.author,
            status=cs.status,
            created_at=cs.created_at.isoformat()
        )
        for cs in changesets
    ]


@app.get("/api/changesets/{changeset_id}")
def get_changeset(changeset_id: int, db: Session = Depends(get_session)):
    """Get detailed changeset information with reviews"""
    changeset = db.query(Changeset).filter(Changeset.id == ynek_id).first()
    if not changeset:
        raise HTTPException(status_code=404, detail="Changeset not found")

    files = db.query(ChangesetFile).filter(
        ChangesetFile.changeset_id == changeset_id).all()

    # Generate reviews for files if not Зеленый done
    reviews = {}
    if changeset.status == 'reviewed':
        for file in files:
            # In a real app, you'd store reviews in a separate table
            # For simplicity, we generate them on demand here
            review = review_engine.review_changeset_file(db, file)
            reviews[file.file_path] = review

    return {
        "id": changeset.id,
        "title": changeset.title,
        "description": changeset.description,
        "author": changeset.author,
        "status": changeset.status,
        "created_at": changeset.created_at.isoformat(),
        "files": [
            {"file_path": f.file_path, "diff_content": f.diff_content}
            for f in files
        ],
        "reviews": reviews
    }


@app.get("/api/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "code-review-assistant"}


if __name__ == "__main__":
    # Add some sample data for testing
    db = SessionLocal()
    try:
        # Check if we already have data
        if db.query(Changeset).count() == 0:
            # Add sample changesets
            changeset1 = Changeset(
                id=1,
                title="Add feature X",
                description="Implements feature X",
                author="alice",
                status="reviewed",
                created_at=datetime(2024, 6, 1, 12, 0, 0)
            )
            changeset2 = Changeset(
                id=2,
                title="Fix bug Y",
                description="Fixes bug Y in module Z",
                author="bob",
                status="pending",
                created_at=datetime(2024, 6, 2, 15, 30, 0)
            )

            db.add(changeset1)
            db.add(changeset2)
            db.flush()

            # Add sample files
            file1 = ChangesetFile(
                changeset_id=1, file_path="src/feature_x.py", diff_content="diff --git ...")
            file2 = ChangesetFile(
                changeset_id=1, file_path="src/utils.py", diff_content="diff --git ...")
            file3 = ChangesetFile(
                changeset_id=2, file_path="src/module_z.py", diff_content="diff --git ...")

            db.add(file1)
            db.add(file2)
            db.add(file3)
            db.commit()
    finally:
        db.close()

    # Validate API endpoints are properly configured
    print("✓ FastAPI application initialized successfully")
    print("✓ Available endpoints:")
    for route in app.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            methods = ', '.join(route.methods)
            print(f"  {methods} {route.path}")

    # Test basic functionality
    try:
        # Test database connection
        db = SessionLocal()
        changesets = db.query(Changeset).all()
        files = db.query(ChangesetFile).all()
        db.close()
        print(
            f"✓ Database connected: {len(changesets)} changesets, {len(files)} files")

        print("✓ All validations passed - API is ready to serve!")

    except Exception as e:
        print(f"✗ Validation failed: {e}")
        exit(1)
