from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime

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

# Session dependency


def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
