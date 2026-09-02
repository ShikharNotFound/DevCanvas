from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.db import get_db
from app.models.project import Project, ProjectStatus
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectOut, ProjectList
from app.utils.deps import get_current_active_user

router = APIRouter()

@router.post("", response_model=ProjectOut, status_code=201)
async def create_project(
    project_data: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    project = Project(
        user_id=current_user.id,
        name=project_data.name,
        description=project_data.description,
        status=ProjectStatus.draft,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project

@router.get("", response_model=ProjectList)
async def list_projects(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    result = await db.execute(
        select(Project).where(Project.user_id == current_user.id).order_by(Project.created_at.desc())
    )
    projects = result.scalars().all()
    return {"projects": projects}

@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    project = await db.get(Project, project_id)
    if not project or project.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    project = await db.get(Project, project_id)
    if not project or project.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Project not found")
    await db.delete(project)
    await db.commit()
    return None