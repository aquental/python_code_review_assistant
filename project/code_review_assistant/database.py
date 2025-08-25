from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime

# Database setup
DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database models
# TODO: Complete the Changeset model with columns for id, title, description, author, status, and created_at
class Changeset(Base):
    __tablename__ = "changesets"
    # Add columns here
    id = Column(Integer, primary_key=True)
    title = Column(String)
    description = Column(Text)
    author = Column(String)
    status = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
# TODO: Complete the ChangesetFile model with columns for id, changeset_id (as foreign key), file_path, and diff_content
class ChangesetFile(Base):
    __tablename__ = "changeset_files"
    # Add columns here
    id = Column(Integer, primary_key=True)
    changeset_id = Column(Integer, ForeignKey("changesets.id"))
    file_path = Column(String)
    diff_content = Column(Text)

# TODO: Add the command to create all database tables
Base.metadata.create_all(bind=engine)

# Session dependency
def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
