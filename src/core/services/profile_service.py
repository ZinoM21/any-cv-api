import json
import re
from typing import Dict, Optional

from fastapi.exceptions import HTTPException, RequestValidationError

from src.core.domain.interfaces import (
    IDataTransformer,
    ILogger,
    IProfileCacheRepository,
    IProfileRepository,
    IRemoteDataSource,
    IUserRepository,
)
from src.core.domain.models import GuestProfile, Profile, UpdateProfile, User
from src.infrastructure.exceptions.handle_exceptions_decorator import handle_exceptions


class ProfileService:
    def __init__(
        self,
        profile_repository: IProfileRepository,
        profile_cache_repository: IProfileCacheRepository,
        user_repository: IUserRepository,
        remote_data_source: IRemoteDataSource,
        logger: ILogger,
        data_transformer: IDataTransformer,
    ):
        self.profile_repository = profile_repository
        self.profile_cache_repository = profile_cache_repository
        self.user_repository = user_repository
        self.remote_data_source = remote_data_source
        self.logger = logger
        self.data_transformer = data_transformer

    def _extract_username(self, link: str) -> str:
        """Extract and validate LinkedIn username from URL or direct input"""
        username = link.strip()

        if "/" in username:
            match = re.match(
                r"^(?:https?:\/\/)?(?:[\w]+\.)?linkedin\.com\/in\/([\w\-]+)\/?.*$",
                username,
            )
            if not match:
                raise RequestValidationError("Invalid LinkedIn URL format")
            return match.group(1)

        if not re.match(r"^[\w\-]+$", username):
            raise RequestValidationError("Invalid username format")

        return username

    @handle_exceptions()
    async def _fetch_and_transform_profile(self, username: str) -> Profile:
        """Fetch and transform profile data from remote data source"""
        raw_profile_data = await self.remote_data_source.get_profile_data_by_username(
            username
        )
        if not raw_profile_data:
            raise HTTPException(
                status_code=500,
                detail="Could not fetch profile data from remote data source",
            )
        self.logger.debug(
            f"Profile data fetched from remote Data Source for: {username}"
        )

        # Transform raw profile data
        profile = await self.data_transformer.transform_profile_data(raw_profile_data)
        if not profile:
            raise HTTPException(
                status_code=500,
                detail="Could not use the fetched data to create a profile",
            )
        self.logger.debug(f"Profile data transformed for: {username}")

        # Check if profile data matches the username
        if profile.username != username:
            raise HTTPException(
                status_code=500,
                detail=f"Fetched data does not match requested username: {username}",
            )

        return profile

    @handle_exceptions()
    async def _create_profile(self, username: str, user: User) -> Dict:
        """Handle profile retrieval/creation for authenticated users"""
        # Check if profile exists
        profile = await self.profile_repository.find_by_username(username)
        if profile:
            self.logger.debug(
                f"Profile record found in db for authenticated user: {username}."
            )
            return json.loads(
                profile.model_dump_json(
                    exclude={"id": True, "updated_at": True, "created_at": True}
                )
            )

        # Otherwise, fetch from LinkedIn & transform
        profile = await self._fetch_and_transform_profile(username)

        # Persist to db
        profile = await self.profile_repository.create(profile)

        # Link the profile to the user
        await self.user_repository.append_profile_to_user(profile, user)
        self.logger.debug(f"Profile record created and linked to user for: {username}")

        return json.loads(profile.model_dump_json(exclude={"updated_at": True}))

    @handle_exceptions()
    async def _create_guest_profile(self, username: str) -> Dict:
        """Handle profile retrieval/creation for guest users"""
        # Check cache / db first
        cached_profile = await self.profile_cache_repository.find_by_username(username)
        if cached_profile:
            self.logger.debug(f"Guest profile record found in cache for: {username}.")
            return json.loads(
                cached_profile.model_dump_json(
                    exclude={"id": True, "updated_at": True, "created_at": True}
                )
            )

        # Otherwise, fetch from LinkedIn & transform
        profile = await self._fetch_and_transform_profile(username)

        # Create guest profile from the data
        guest_profile = GuestProfile(
            **json.loads(
                profile.model_dump_json(
                    exclude={"id": True, "updated_at": True, "created_at": True}
                )
            )
        )

        # Persist to cache
        guest_profile = await self.profile_cache_repository.create(guest_profile)
        self.logger.debug(f"Guest profile record created for: {username}")

        return json.loads(guest_profile.model_dump_json(exclude={"updated_at": True}))

    # Public methods
    @handle_exceptions()
    async def create_profile(self, link: str, user: Optional[User] = None) -> Dict:
        """Create a profile by username with data from data broker. Uses db as cache."""
        username = self._extract_username(link)
        self.logger.debug(f"Extracted username: {username}")

        if user:
            return await self._create_profile(username, user)

        return await self._create_guest_profile(username)

    @handle_exceptions()
    async def get_profile(self, username: str, user: Optional[User] = None) -> Dict:
        """Get a profile by username from database"""
        if user:
            profile = await self.profile_repository.find_by_username(username)

        else:
            profile = await self.profile_cache_repository.find_by_username(username)

        if not profile:
            raise HTTPException(
                status_code=404, detail=f"Profile not found for username: {username}"
            )

        return json.loads(profile.model_dump_json(exclude={"updated_at": True}))

    @handle_exceptions()
    async def update_profile(
        self, username: str, data: UpdateProfile, user: Optional[User] = None
    ) -> dict:
        """
        Update a user profile with the partial data.
        Updates guest_profile document if user is not authenticated.
        """
        data_to_update = data.model_dump(
            exclude_unset=True,
        )

        if user:
            profile = await self.profile_repository.find_by_username(username)

            if not profile:
                raise HTTPException(
                    status_code=404,
                    detail=f"Profile not found for username: {username}",
                )

            updated_profile = await self.profile_repository.update(
                profile, data_to_update
            )

        else:
            guest_profile = await self.profile_cache_repository.find_by_username(
                username
            )

            if not guest_profile:
                raise HTTPException(
                    status_code=404,
                    detail=f"Profile not found for username: {username}",
                )

            updated_profile = await self.profile_cache_repository.update(
                guest_profile, data_to_update
            )

        return json.loads(updated_profile.model_dump_json(exclude={"updated_at": True}))
