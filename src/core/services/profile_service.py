import re
from typing import Optional

from fastapi.exceptions import HTTPException, RequestValidationError

from src.core.domain.dtos import UpdateProfile
from src.core.domain.interfaces import (
    IDataTransformer,
    ILogger,
    IProfileCacheRepository,
    IProfileRepository,
    IRemoteDataSource,
    IUserRepository,
)
from src.core.domain.models import GuestProfile, Profile, User
from src.infrastructure.exceptions import handle_exceptions


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
    async def _fetch_and_transform_profile(
        self,
        username: str,
        is_authenticated: bool = False,
        user_id: Optional[str] = None,
    ) -> Profile:
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
        profile = await self.data_transformer.transform_profile_data(
            data=raw_profile_data, is_authenticated=is_authenticated, user_id=user_id
        )
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
    def _user_has_access_to_profile(self, user: User, profile: Profile) -> bool:
        if user:
            for p in user.profiles:  # type: ignore
                if p.id == profile.id:
                    return True
        return False

    @handle_exceptions()
    async def _create_profile(self, username: str, user: User) -> dict:
        """Handle profile retrieval/creation for authenticated users"""
        # Check if profile exists
        profile = self.profile_repository.find_by_username(username)
        if profile:
            self.logger.debug(
                f"Profile record found in db for authenticated user: {username}."
            )
            return profile.to_mongo().to_dict()

        # Otherwise, fetch from LinkedIn & transform
        profile = await self._fetch_and_transform_profile(
            username=username, is_authenticated=True, user_id=str(user.id)
        )

        # Persist to db
        profile = self.profile_repository.create(profile)

        # Link the profile to the user
        self.user_repository.append_profile_to_user(profile, user)
        self.logger.debug(f"Profile record created and linked to user for: {username}")

        profile = self.profile_repository.find_by_username(username)
        if not profile:
            raise HTTPException(
                status_code=500,
                detail=f"Profile not found for username: {username}",
            )

        return profile.to_mongo().to_dict()

    @handle_exceptions()
    async def _create_guest_profile(self, username: str) -> dict:
        """Handle profile retrieval/creation for guest users"""
        # Check cache / db first
        cached_profile = self.profile_cache_repository.find_by_username(username)
        if cached_profile:
            self.logger.debug(f"Guest profile record found in cache for: {username}.")
            return cached_profile.to_mongo().to_dict()

        # Otherwise, fetch from LinkedIn & transform
        profile = await self._fetch_and_transform_profile(username=username)

        # Create guest profile from the data
        guest_profile = GuestProfile(
            username=profile.username,
            firstName=profile.firstName,
            lastName=profile.lastName,
            profilePictureUrl=profile.profilePictureUrl,
            jobTitle=profile.jobTitle,
            headline=profile.headline,
            about=profile.about,
            email=profile.email,
            phone=profile.phone,
            location=profile.location,
            languages=profile.languages,
            experiences=profile.experiences,
            education=profile.education,
            skills=profile.skills,
            volunteering=profile.volunteering,
            projects=profile.projects,
        )

        # Persist to cache
        guest_profile = self.profile_cache_repository.create(guest_profile)
        self.logger.debug(f"Guest profile record created for: {username}")

        return guest_profile.to_mongo().to_dict()

    # Public methods
    @handle_exceptions()
    async def create_profile(self, link: str, user: Optional[User] = None) -> dict:
        """Create a profile by username with data from data broker. Uses db as cache."""
        username = self._extract_username(link)
        self.logger.debug(f"Extracted username: {username}")

        is_authenticated = user is not None

        if is_authenticated:
            return await self._create_profile(username, user)

        return await self._create_guest_profile(username)

    @handle_exceptions()
    async def get_profile(self, username: str, user: Optional[User] = None) -> dict:
        """Get a profile by username from database"""
        if user:
            profile = self.profile_repository.find_by_username(username)
            if not profile:
                raise HTTPException(
                    status_code=404,
                    detail=f"Profile not found for username: {username}",
                )
            if not self._user_has_access_to_profile(user, profile):
                raise HTTPException(
                    status_code=403,
                    detail=f"User does not have access to profile: {username}",
                )

        else:
            profile = self.profile_cache_repository.find_by_username(username)
            if not profile:
                raise HTTPException(
                    status_code=404,
                    detail=f"Profile not found for username: {username}",
                )

        return profile.to_mongo().to_dict()

    @handle_exceptions()
    async def get_published_profiles(self) -> list[dict]:
        """Get all published profiles"""
        profiles = self.profile_repository.find_published_profiles()
        return [profile.to_mongo().to_dict() for profile in profiles]

    @handle_exceptions()
    async def get_published_profile(self, username: str) -> dict:
        """Get a published profile"""
        profile = self.profile_repository.find_published_by_username(username)
        if not profile:
            raise HTTPException(
                status_code=404,
                detail=f"Profile not found for username: {username}",
            )
        return profile.to_mongo().to_dict()

    @handle_exceptions()
    async def update_profile(
        self, username: str, data: UpdateProfile, user: Optional[User] = None
    ) -> dict:
        """
        Update a user profile with the partial data.
        Updates guest_profile document if user is not authenticated.
        """
        data_to_update = data.model_dump(
            mode="json",
            exclude_unset=True,
            exclude_none=True,
        )

        if user:
            profile = self.profile_repository.find_by_username(username)
            if not profile:
                raise HTTPException(
                    status_code=404,
                    detail=f"Profile not found for username: {username}",
                )
            if not self._user_has_access_to_profile(user, profile):
                raise HTTPException(
                    status_code=403,
                    detail=f"User does not have access to profile: {username}",
                )

            updated_profile = self.profile_repository.update(profile, data_to_update)

        else:
            guest_profile = self.profile_cache_repository.find_by_username(username)

            if not guest_profile:
                raise HTTPException(
                    status_code=404,
                    detail=f"Profile not found for username: {username}",
                )

            updated_profile = self.profile_cache_repository.update(
                guest_profile, data_to_update
            )

        return updated_profile.to_mongo().to_dict()

    @handle_exceptions()
    async def transfer_guest_profile_to_user(self, username: str, user: User) -> dict:
        """
        Transfer a guest profile to a user profile after sign-in.
        1. Find the guest profile
        2. Create a new Profile entry
        3. Link it to the user
        4. Delete the guest profile
        5. Return the new profile
        """
        # Check if guest profile exists
        guest_profile = self.profile_cache_repository.find_by_username(username)
        if not guest_profile:
            raise HTTPException(
                status_code=404,
                detail=f"Guest profile not found for username: {username}",
            )

        self.logger.debug(f"Found guest profile for username: {username}")

        # Check if user already has this profile
        existing_profile = self.profile_repository.find_by_username(username)
        if existing_profile:
            # If profile already exists, check if user has access
            if self._user_has_access_to_profile(user, existing_profile):
                self.logger.debug(f"User already has access to profile: {username}")
                # User already has this profile, delete the guest profile
                self.profile_cache_repository.delete(guest_profile)
                return existing_profile.to_mongo().to_dict()

        # Create the new profile from the guest profile
        new_profile = Profile(
            username=guest_profile.username,
            firstName=guest_profile.firstName,
            lastName=guest_profile.lastName,
            profilePictureUrl=guest_profile.profilePictureUrl,
            jobTitle=guest_profile.jobTitle,
            headline=guest_profile.headline,
            about=guest_profile.about,
            email=guest_profile.email,
            phone=guest_profile.phone,
            location=guest_profile.location,
            languages=guest_profile.languages,
            experiences=guest_profile.experiences,
            education=guest_profile.education,
            skills=guest_profile.skills,
            volunteering=guest_profile.volunteering,
            projects=guest_profile.projects,
        )
        profile = self.profile_repository.create(new_profile)

        # Link profile to user
        self.user_repository.append_profile_to_user(profile, user)
        self.logger.debug(f"Profile linked to user for username: {username}")

        # Delete the guest profile
        self.profile_cache_repository.delete(guest_profile)
        self.logger.debug(f"Guest profile deleted for username: {username}")

        return profile.to_mongo().to_dict()

    @handle_exceptions()
    async def get_user_profiles(self, user: User) -> list[dict]:
        """
        Get all profiles associated with the user.
        """
        if not user or not hasattr(user, "profiles") or not user.profiles:
            return []

        profiles = []
        # User.profiles is a list of references
        for profile_ref in user.profiles:  # type: ignore
            profile = self.profile_repository.find_by_id(str(profile_ref.id))
            if profile:
                profiles.append(profile.to_mongo().to_dict())

        return profiles
