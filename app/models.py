"""Database models for ReQperacion."""

import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, BigInteger, DateTime, ForeignKey, Index
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://reqperacion_user:reqperacion_pass@localhost:3306/reqperacion"
)

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    files = relationship("File", back_populates="owner", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"


class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size = Column(BigInteger, default=0)
    description = Column(Text, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    last_accessed = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processing_status = Column(String(20), default="pending", nullable=False)

    owner = relationship("User", back_populates="files")
    extracted_texts = relationship("ExtractedText", back_populates="file", cascade="all, delete-orphan")
    tags = relationship("FileTag", back_populates="file", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_user_id", "user_id"),
        Index("idx_file_type", "file_type"),
        Index("idx_processing_status", "processing_status"),
    )

    def __repr__(self):
        return f"<File(id={self.id}, name='{self.original_filename}', status='{self.processing_status}')>"


class ExtractedText(Base):
    __tablename__ = "extracted_texts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_id = Column(Integer, ForeignKey("files.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text().with_variant(mysql.LONGTEXT, "mysql"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    file = relationship("File", back_populates="extracted_texts")

    def __repr__(self):
        return f"<ExtractedText(id={self.id}, file_id={self.file_id})>"


class FileTag(Base):
    __tablename__ = "file_tags"

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_id = Column(Integer, ForeignKey("files.id", ondelete="CASCADE"), nullable=False)
    tag = Column(String(100), nullable=False, index=True)

    file = relationship("File", back_populates="tags")

    def __repr__(self):
        return f"<FileTag(id={self.id}, tag='{self.tag}')>"


def init_db():
    """Create all tables if they don't exist."""
    Base.metadata.create_all(bind=engine)


def get_session():
    """Get a new database session."""
    db = SessionLocal()
    try:
        return db
    except Exception:
        db.close()
        raise
