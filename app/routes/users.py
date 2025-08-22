from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any
from ..models import (
    UserProfile,
    UserProfileResponse,
    UsersListResponse,
    ProfileSetupRequest,
    ProfileSetupResponse,
    CVPUserSummary,
    CVPUsersListResponse,
    DeleteUserResponse,
)
from ..database import mongodb
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/user", tags=["users"])

@router.post("/setup", response_model=ProfileSetupResponse, status_code=status.HTTP_201_CREATED)
async def setup_profile(payload: ProfileSetupRequest):
    """Step 0: Profile setup for CVP Lite journey.
    Creates or updates a user profile with the provided information.
    """
    try:
        # Compose a student_id if not provided: firstpart-lastpart-grade with timestamp suffix
        student_id = payload.student_id
        if not student_id:
            safe_first = payload.first_name.strip().lower().replace(" ", "")[:12]
            safe_last = payload.last_name.strip().lower().replace(" ", "")[:12]
            safe_grade = str(payload.grade).strip().lower()
            from datetime import datetime
            suffix = datetime.utcnow().strftime("%Y%m%d%H%M%S")
            student_id = f"{safe_first}-{safe_last}-{safe_grade}-{suffix}"

        # Build storage document adhering to existing collection shape
        name_combined = f"{payload.first_name.strip()} {payload.last_name.strip()}".strip()
        user_document: Dict[str, Any] = {
            "student_id": student_id,
            "name": name_combined,
            # Retain legacy-compatible fields for this codebase
            "favorite_foods": [],
            "dietary_preferences": [],
            # CVP Lite specific fields
            "grade": str(payload.grade).strip(),
            "school_name": payload.school_name.strip(),
            "email": payload.email.strip(),
            "phone": (payload.phone or "").strip(),
            "city": (payload.city or "").strip(),
            "country": (payload.country or "").strip(),
            "subject_stream": (payload.subject_stream or "").strip(),
            "hobbies_and_passions": payload.hobbies_and_passions,
            "dream_job": (payload.dream_job or "").strip(),
            "future_self_info": (payload.future_self_info or "").strip(),
            # Journey tracking - Removed step tracking
            "cvp_lite": {
                # "current_step": 0,  # Removed step tracking
                # "steps_completed": [],  # Removed step tracking
            },
        }

        ok = mongodb.create_or_update_user(user_document)
        if not ok:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to persist profile")

        # Build formatted response message
        student_name = name_combined
        city_text = (payload.city or "").strip()
        country_text = (payload.country or "").strip()
        location_text = f"{city_text}, {country_text}".strip(", ") if (city_text or country_text) else "—"
        stream_text = (payload.subject_stream or "—").strip() or "—"
        hobbies_text = ", ".join(payload.hobbies_and_passions) if payload.hobbies_and_passions else "—"
        dream_job_text = (payload.dream_job or "—").strip() or "—"
        future_self_text = (payload.future_self_info or "—").strip() or "—"

        response_text = (
            "Amazing! Your Profile is Complete\n"
            "Here's what I learned about you:\n"
            f"** Meet {student_name}**\n"
            f"- Grade {str(payload.grade).strip()} student at {payload.school_name.strip()}\n"
            f"- Lives in {location_text}\n"
            f"- Currently interested in: {stream_text}\n"
            f"- Passionate about: {hobbies_text}\n"
            f"- Dreams of: {dream_job_text}\n"
            f"- Future Vision: {future_self_text}\n\n"
            f"**Your YPD ID: {student_id}**\n"
            "*This information will help create the most relevant and personal career guidance for you.*\n\n"
            "## Ready to Begin?\n"
            "You're all set to start your career guidance journey!\n\n"
            "Your profile information will be used to provide personalized insights and recommendations.\n"
        )

        return ProfileSetupResponse(student_id=student_id, message=response_text)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in profile setup: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get("/", response_model=CVPUsersListResponse)
async def get_all_users():
    """Get all user profiles"""
    try:
        users = mongodb.get_all_users()
        summaries: list[CVPUserSummary] = []
        for doc in users:
            cvp_meta = (doc.get("cvp_lite") or {}) if isinstance(doc, dict) else {}
            summaries.append(CVPUserSummary(
                student_id=doc.get("student_id", ""),
                name=doc.get("name", ""),
                grade=str(doc.get("grade")) if doc.get("grade") is not None else None,
                school_name=doc.get("school_name"),
                city=doc.get("city"),
                country=doc.get("country"),
                subject_stream=doc.get("subject_stream"),
                hobbies_and_passions=doc.get("hobbies_and_passions", []) or [],
                dream_job=doc.get("dream_job"),
                future_self_info=doc.get("future_self_info"),
                # current_step=cvp_meta.get("current_step"),  # Removed step tracking
                created_at=doc.get("created_at"),
                updated_at=doc.get("updated_at"),
            ))

        return CVPUsersListResponse(users=summaries, total_count=len(summaries))
        
    except Exception as e:
        logger.error(f"Error retrieving all users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/{user_id}", response_model=UserProfileResponse)
async def get_user(user_id: str):
    """Get user profile by student_id"""
    try:
        user = mongodb.get_user(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with student_id {user_id} not found"
            )
        
        # Handle migration from favorite_food to favorite_foods
        if 'favorite_food' in user and 'favorite_foods' not in user:
            user['favorite_foods'] = [user['favorite_food']]
            del user['favorite_food']
            # Update the user in database
            mongodb.create_or_update_user(user)
        
        # Ensure favorite_foods exists
        if 'favorite_foods' not in user:
            user['favorite_foods'] = []
        
        return UserProfileResponse(**user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/", response_model=UserProfileResponse)
async def create_or_update_user(user: UserProfile):
    """Create or update user profile"""
    try:
        # Convert Pydantic model to dict
        user_data = user.dict()
        
        # Create or update user in MongoDB
        success = mongodb.create_or_update_user(user_data)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create/update user profile"
            )
        
        # Retrieve the updated user data
        updated_user = mongodb.get_user(user.student_id)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve updated user profile"
            )
        return UserProfileResponse(**updated_user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating/updating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        ) 

@router.delete("/{user_id}", response_model=DeleteUserResponse, status_code=status.HTTP_200_OK)
async def delete_user(user_id: str):
    """Delete a user by student_id. Returns confirmation when successful."""
    try:
        deleted = mongodb.delete_user(user_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with student_id {user_id} not found"
            )
        return DeleteUserResponse(student_id=user_id, message="User deleted successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )