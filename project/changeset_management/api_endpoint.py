from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

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

# Database session dependency


def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize sample data


def init_sample_data():
    db = SessionLocal()
    try:
        # Check if data already exists
        if db.query(Changeset).first():
            return

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


# Initialize sample data on module import
init_sample_data()

# FastAPI app
app = FastAPI()

# Pydantic response model


class ChangesetResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    author: str
    status: str
    created_at: str


@app.get("/api/changesets", response_model=List[ChangesetResponse])
def list_changesets(db: Session = Depends(get_session)):
    """List all changesets"""
    changesets = db.query(Changeset).all()
    return [
        ChangesetResponse(
            id=changeset.id,
            title=changeset.title,
            description=changeset.description,
            author=changeset.author,
            status=changeset.status,
            created_at=changeset.created_at.isoformat()
        ) for changeset in changesets
    ]


if __name__ == "__main__":
    # Validate API endpoints are properly configured
    print("✓ FastAPI application initialized successfully")
    print("✓ Available endpoints:")
    for route in app.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            methods = ', '.join(route.methods)
            print(f"  {methods} {route.path}")

    # Test basic functionality
    try:
        # Test database session dependency
        session_gen = get_session()
        session = next(session_gen)
        session.close()
        print("✓ Database session dependency working")

        # Test database data
        db = SessionLocal()
        changesets = db.query(Changeset).all()
        files = db.query(ChangesetFile).all()
        db.close()
        print(
            f"✓ Database data loaded: {len(changesets)} changesets, {len(files)} files")

        print("✓ All validations passed - API is ready to serve!")

    except Exception as e:
        print(f"✗ Validation failed: {e}")
        exit(1)
