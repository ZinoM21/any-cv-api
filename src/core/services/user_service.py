from datetime import datetime, timezone
from uuid import UUID

from fastapi import status

from src.core.domain.interfaces import (
    IUserRepository,
)
from src.core.dtos import UserResponse, UserUpdate
from src.core.exceptions import (
    HTTPException,
    HTTPExceptionType,
    handle_exceptions,
)
from src.core.interfaces import (
    ILogger,
    IProfileService,
    IUserService,
)


class UserService(IUserService):
    def __init__(
        self,
        user_repository: IUserRepository,
        profile_service: IProfileService,
        logger: ILogger,
    ):
        self.user_repository = user_repository
        self.profile_service = profile_service
        self.logger = logger

    @handle_exceptions(origin="UserService.get_user")
    async def get_user(self, user_id: str) -> UserResponse:
        """Get a user's information.

        Args:
            user_id: The ID of the user

        Returns:
            UserResponse: The user's information

        Raises:
            HTTPException: If the user doesn't exist
        """
        user = self.user_repository.find_by_id(user_id)
        if not user:
            self.logger.error(f"User not found: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=HTTPExceptionType.ResourceNotFound.value,
            )

        return UserResponse(
            id=UUID(str(user.id)),
            email=str(user.email),
            firstName=str(user.firstName),
            lastName=str(user.lastName),
            email_verified=bool(user.email_verified),
        )

    @handle_exceptions(origin="UserService.update_user")
    async def update_user(self, user_id: str, user_data: UserUpdate) -> UserResponse:
        """Updates a user's account information.

        Args:
            user_id: The ID of the user to update
            user_data: The updated user data

        Returns:
            UserResponse: The updated user data

        Raises:
            HTTPException: If the user doesn't exist or there's a validation error
        """
        user = self.user_repository.find_by_id(user_id)
        if not user:
            self.logger.error(f"User not found for update: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=HTTPExceptionType.ResourceNotFound.value,
            )

        # Create a dict with only the non-None fields
        update_data = {}
        for field, value in user_data.model_dump(exclude_none=True).items():
            if value is not None:
                update_data[field] = value

        if not update_data:
            self.logger.info("No data provided for user update")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=HTTPExceptionType.BadRequest.value,
            )

        # Add updated_at to the update data
        update_data["updated_at"] = datetime.now(timezone.utc)

        # Update the user
        updated_user = self.user_repository.update(user, update_data)
        if not updated_user:
            self.logger.error(f"Failed to update user: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=HTTPExceptionType.InternalServerError.value,
            )

        self.logger.info(f"User account updated successfully: {user.email}")
        return UserResponse(
            id=UUID(str(updated_user.id)),
            email=str(updated_user.email),
            firstName=str(updated_user.firstName),
            lastName=str(updated_user.lastName),
            email_verified=bool(updated_user.email_verified),
        )

    @handle_exceptions(origin="UserService.delete_user")
    async def delete_user(self, user_id: str) -> None:
        """Delete a user and all associated profiles.

        Args:
            user_id: The ID of the user to delete

        Raises:
            HTTPException: If the user doesn't exist or there's an error during deletion
        """
        user = self.user_repository.find_by_id(user_id)
        if not user:
            # self.logger.error(f"User not found for deletion: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=HTTPExceptionType.ResourceNotFound.value,
            )

        # Delete all profiles associated with the user, including files
        await self.profile_service.delete_profiles_from_user(user)

        # Delete the user
        self.user_repository.delete(user)
        self.logger.debug(f"User account deleted successfully: {user.email}")

        return None
