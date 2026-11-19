from sqlalchemy import Column, Integer, String , ForeignKey
from app.database import Base


class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String(255), nullable=False)

    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    description = Column(String(1000), nullable=True)

    file_name = Column(String(255), nullable=False)

    file_size = Column(Integer, nullable=False)

    content_type = Column(String(100), nullable=False)

    status = Column(String(50), nullable=False, default="processing")

    low_file_path = Column(String(500), nullable=True)

    medium_file_path = Column(String(500), nullable=True)

    high_file_path = Column(String(500), nullable=True)

    content_hash = Column(String(64), nullable=True, unique=True)