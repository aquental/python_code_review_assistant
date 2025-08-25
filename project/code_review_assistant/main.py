from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session, sessionmaker, declarative_base
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from datetime import datetime
from schemas import FileChangeRequest, ChangesetRequest

# --- Database setup (minimal for runnable example) ---
DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Models ---


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


# Create tables
Base.metadata.create_all(bind=engine)

# --- Review Engine Stub ---


class ReviewEngine:
    def review_full_changeset(self, db, changeset_id):
        # Dummy review logic
        return {"result": "reviewed"}


# --- FastAPI app ---
app = FastAPI(title="Code Review Assistant", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

review_engine = ReviewEngine()


@app.post("/api/changesets", response_model=dict)
def submit_changeset(
    request: ChangesetRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_session)
):
    """Submit a new changeset for review"""
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

    # Process review in background
    background_tasks.add_task(process_changeset_review, changeset.id)

    return {"message": "Changeset submitted", "changeset_id": changeset.id}


def process_changeset_review(changeset_id: int):
    """Background task to process changeset review"""
    db = SessionLocal()
    try:
        reviews = review_engine.review_full_changeset(db, changeset_id)
        # Store reviews in a separate table or update changeset status
        changeset = db.query(Changeset).filter_by(id=changeset_id).first()
        if changeset:
            changeset.status = 'reviewed'
            db.commit()
    finally:
        db.close()
