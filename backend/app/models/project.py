import uuid
import enum
from datetime import datetime
from sqlalchemy import String, Text, Enum as SAEnum, DateTime, ForeignKey, func, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base

class ProjectStatus(str, enum.Enum):
    draft = "draft"
    generating = "generating"
    completed = "completed"
    failed = "failed"

class Project(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[ProjectStatus] = mapped_column(SAEnum(ProjectStatus), default=ProjectStatus.draft, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", backref="projects")