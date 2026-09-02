from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class ProjectCreate(BaseModel):
    name : str
    description : str


class ProjectOut(BaseModel):
    id: UUID
    name: str
    description: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProjectList(BaseModel):
    projects: list[ProjectOut]