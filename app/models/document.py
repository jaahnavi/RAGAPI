from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime, timezone
from app.database import Base

class Documents(Base):
    __tablename__="documents"

    id = Column(Integer, primary_key=True)
    uuid = Column(String, unique=True)
    filename = Column(String)
    filepath = Column(String, nullable=True)
    source_url = Column(String, nullable=True, unique=True)
    content_hash = Column(String, nullable=True, unique=True)
    source_type = Column(String, default="upload")  # "seed" or "upload"
    status = Column(String, default="processing")  # processing / ready / failed
    error = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


