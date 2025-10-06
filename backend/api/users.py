from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr
from uuid import UUID
from typing import Optional

from db.database import get_db
from db.models import User, UserProfile
from embeddings.service import embedding_service

router = APIRouter()


class CreateUserRequest(BaseModel):
    email: EmailStr
    full_name: str


class CreateProfileRequest(BaseModel):
    resume_text: str
    skills: list[str]
    experience: dict
    education: dict
    career_goals: str
    preferences: dict


@router.post("/")
async def create_user(
    request: CreateUserRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a new user"""
    # Check if user exists
    result = await db.execute(
        select(User).where(User.email == request.email)
    )
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    user = User(
        email=request.email,
        full_name=request.full_name,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "created_at": user.created_at,
    }


@router.get("/{user_id}")
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get user details"""
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "created_at": user.created_at,
    }


@router.post("/{user_id}/profile")
async def create_profile(
    user_id: UUID,
    request: CreateProfileRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create or update user profile with embeddings"""
    # Verify user exists
    user_result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Generate embeddings
    skills_text = ", ".join(request.skills)
    experience_text = str(request.experience)
    
    embeddings = await embedding_service.embed_profile(
        skills=skills_text,
        experience=experience_text,
        goals=request.career_goals,
    )
    
    # Check if profile exists
    profile_result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == user_id)
    )
    profile = profile_result.scalar_one_or_none()
    
    if profile:
        # Update existing profile
        profile.resume_text = request.resume_text
        profile.skills = request.skills
        profile.experience = request.experience
        profile.education = request.education
        profile.career_goals = request.career_goals
        profile.preferences = request.preferences
        profile.skills_embedding = embeddings["skills_embedding"]
        profile.experience_embedding = embeddings["experience_embedding"]
        profile.goals_embedding = embeddings["goals_embedding"]
    else:
        # Create new profile
        profile = UserProfile(
            user_id=user_id,
            resume_text=request.resume_text,
            skills=request.skills,
            experience=request.experience,
            education=request.education,
            career_goals=request.career_goals,
            preferences=request.preferences,
            skills_embedding=embeddings["skills_embedding"],
            experience_embedding=embeddings["experience_embedding"],
            goals_embedding=embeddings["goals_embedding"],
        )
        db.add(profile)
    
    await db.commit()
    await db.refresh(profile)
    
    return {
        "id": str(profile.id),
        "user_id": str(profile.user_id),
        "created_at": profile.created_at,
        "updated_at": profile.updated_at,
    }


@router.get("/{user_id}/profile")
async def get_profile(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get user profile"""
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    return {
        "id": str(profile.id),
        "user_id": str(profile.user_id),
        "skills": profile.skills,
        "experience": profile.experience,
        "education": profile.education,
        "career_goals": profile.career_goals,
        "preferences": profile.preferences,
        "created_at": profile.created_at,
        "updated_at": profile.updated_at,
    }
