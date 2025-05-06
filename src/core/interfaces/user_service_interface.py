from abc import ABC, abstractmethod

from ..dtos import UserResponse, UserUpdate


class IUserService(ABC):
    @abstractmethod
    async def get_user(self, user_id: str) -> UserResponse:
        """Get a user by id"""
        pass

    @abstractmethod
    async def update_user(self, user_id: str, user_data: UserUpdate) -> UserResponse:
        """Update a user"""
        pass

    @abstractmethod
    async def delete_user(self, user_id: str) -> None:
        """Delete a user"""
        pass
