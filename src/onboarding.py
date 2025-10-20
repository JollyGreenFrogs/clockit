"""
Onboarding API endpoints for new users
"""

from typing import List
from fastapi import HTTPException
from pydantic import BaseModel


class OnboardingData(BaseModel):
    """User onboarding data"""
    default_category: str
    initial_categories: List[str] = []  # Optional initial categories to create


class OnboardingStatus(BaseModel):
    """User onboarding status response"""
    onboarding_completed: bool
    default_category: str | None = None
    needs_onboarding: bool


def create_onboarding_endpoints(app, get_current_user, auth_service, task_manager):
    """Create onboarding-related API endpoints"""

    @app.get("/onboarding/status")
    async def get_onboarding_status(current_user=get_current_user()):
        """Get user's onboarding status"""
        try:
            return OnboardingStatus(
                onboarding_completed=current_user.onboarding_completed,
                default_category=current_user.default_category,
                needs_onboarding=not current_user.onboarding_completed
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error getting onboarding status: {str(e)}")

    @app.post("/onboarding/complete")
    async def complete_onboarding(
        onboarding_data: OnboardingData,
        current_user=get_current_user()
    ):
        """Complete user onboarding"""
        try:
            # Update user's onboarding status and default category
            success = auth_service.complete_user_onboarding(
                user_id=str(current_user.id),
                default_category=onboarding_data.default_category
            )
            
            if not success:
                raise HTTPException(status_code=500, detail="Failed to complete onboarding")

            # Create initial categories if provided
            for category_name in onboarding_data.initial_categories:
                if category_name.strip():
                    task_manager.create_category(
                        name=category_name.strip(),
                        description="Category created during onboarding",
                        color="#007bff"  # Default blue color
                    )

            return {
                "message": "Onboarding completed successfully",
                "default_category": onboarding_data.default_category,
                "categories_created": len(onboarding_data.initial_categories)
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error completing onboarding: {str(e)}")

    @app.get("/onboarding/check")
    async def check_onboarding_required(current_user=get_current_user()):
        """Check if user needs onboarding (used by frontend for routing)"""
        return {
            "requires_onboarding": not current_user.onboarding_completed,
            "user_id": str(current_user.id),
            "username": current_user.username
        }