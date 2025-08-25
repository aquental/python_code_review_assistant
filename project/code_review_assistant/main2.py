from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from database import get_session, Changeset, ChangesetFile, SessionLocal
from schemas import ChangesetRequest
from review_engine import ReviewEngine

# Create FastAPI app
app = FastAPI(title="Code Review Assistant", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize review engine
review_engine = ReviewEngine()

def process_changeset_review(changeset_id: int):
    """Background task to process changeset review"""
    # Create a new database session using SessionLocal
    db = SessionLocal()
    
    try:
        # Call the review engine to process the changeset
        reviews = review_engine.review_full_changeset(db, changeset_id)
        
        # Update the changeset status to 'reviewed'
        changeset = db.query(Changeset).filter_by(id=changeset_id).first()
        if changeset:
            changeset.status = 'reviewed'
            db.commit()
    
    # Add proper exception handling with rollback
    except Exception as e:
        db.rollback()
        print(f"Error processing review for changeset {changeset_id}: {str(e)}")
    
    # Ensure the database session is closed in a finally block
    finally:
        db.close()

@app.post("/api/changesets", response_model=dict)
def submit_changeset(
    request: ChangesetRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_session)
):
    """Submit a new changeset for review"""
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
        
        # TODO: Add the background task to process the review
        background_tasks.add_task(process_changeset_review, changeset.id)
        
        return {"message": "Changeset submitted", "changeset_id": changeset.id}
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/changesets/{changeset_id}", response_model=dict)
def get_changeset(changeset_id: int, db: Session = Depends(get_session)):
    """Get a changeset by ID"""
    changeset = db.query(Changeset).filter_by(id=changeset_id).first()
    if not changeset:
        raise HTTPException(status_code=404, detail="Changeset not found")
    
    return {
        "id": changeset.id,
        "title": changeset.title,
        "description": changeset.description,
        "author": changeset.author,
        "status": changeset.status,
        "created_at": changeset.created_at.isoformat()
    }
