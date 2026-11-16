from sqlalchemy import Column, DateTime, Integer, String, func

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    email = Column(String(255), nullable=False, unique=True, index=True)

    hashed_password = Column(String(255), nullable=False)

    created_at = Column(DateTime, nullable=False, server_default=func.now())