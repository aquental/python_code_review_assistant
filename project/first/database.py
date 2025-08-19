from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from project.first.models import Base

DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///code_review.db')
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def init_database():
    Base.metadata.create_all(bind=engine)


def get_session():
    return SessionLocal()
