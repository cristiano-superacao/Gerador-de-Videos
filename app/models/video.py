from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class VideoJob(Base):
    __tablename__ = "video_jobs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    source_type = Column(String(20), nullable=False)
    source_content = Column(Text, nullable=False)
    script_variant = Column(Integer, nullable=False)
    status = Column(String(30), default="queued", nullable=False)
    provider = Column(String(50), default="shotstack", nullable=False)
    render_id = Column(String(120), nullable=True, index=True)
    output_url = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User")
