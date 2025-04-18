import re
from typing import Optional

from fastapi import HTTPException, status
from fastapi.exceptions import RequestValidationError

from src.config import Settings
from src.core.domain.dtos import PublishingOptionsUpdate, UpdateProfile
from src.core.domain.interfaces import (
    IDataTransformer,
    IFileService,
    ILogger,
    IProfileCacheRepository,
    IProfileRepository,
    IRemoteDataSource,
    IUserRepository,
)
from src.core.domain.models import GuestProfile, Profile, User
from src.infrastructure.exceptions import (
    ApiErrorType,
    handle_exceptions,
)


class ProfileService:
    def __init__(
        self,
        profile_repository: IProfileRepository,
        profile_cache_repository: IProfileCacheRepository,
        user_repository: IUserRepository,
        remote_data_source: IRemoteDataSource,
        file_service: IFileService,
        data_transformer: IDataTransformer,
        logger: ILogger,
        settings: Settings,
    ):
        self.profile_repository = profile_repository
        self.profile_cache_repository = profile_cache_repository
        self.user_repository = user_repository
        self.remote_data_source = remote_data_source
        self.file_service = file_service
        self.data_transformer = data_transformer
        self.logger = logger
        self.settings = settings

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
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=ApiErrorType.ServiceUnavailable.value,
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
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not use the fetched data to create a profile",
            )
        self.logger.debug(f"Profile data transformed for: {username}")

        # Check if profile data matches the username
        if profile.username != username:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
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
    async def _get_profile_from_user_by_username(
        self, username: str, user: User
    ) -> Optional[Profile]:
        profile_ids = [str(p.id) for p in user.profiles]  # type: ignore
        profiles = self.profile_repository.find_by_ids_and_username(
            profile_ids, username
        )
        if profiles:
            # profiles should only have one entry since username is unique
            return profiles[0]
        return None

    @handle_exceptions()
    def _get_all_profile_files(self, profile: Profile) -> list[str]:
        """Get all files associated with a profile as a list of strings"""
        all_files: list[str] = []

        if profile.profilePictureUrl:  # type: ignore
            all_files.append(profile.profilePictureUrl)  # type: ignore

        for exp in profile.experiences:  # type: ignore
            if exp.companyLogoUrl:
                all_files.append(exp.companyLogoUrl)

        for edu in profile.education:  # type: ignore
            if edu.schoolPictureUrl:
                all_files.append(edu.schoolPictureUrl)

        for vol in profile.volunteering:  # type: ignore
            if vol.organizationLogoUrl:
                all_files.append(vol.organizationLogoUrl)

        for proj in profile.projects:  # type: ignore
            if proj.thumbnail:
                all_files.append(proj.thumbnail)

        return [file for file in all_files if file]

    @handle_exceptions()
    async def _make_files_public(self, profile: Profile) -> None:
        """Make files public"""
        self.logger.debug(f"Making files public for profile: {profile.username}")
        all_files: list[str] = self._get_all_profile_files(profile)

        for file in all_files:
            if file:
                self.logger.debug(f"Copying file to public: {file}")
                await self.file_service.copy_files_from_private_to_public(file)

    @handle_exceptions()
    async def _create_profile_for_user_from_remote_data(
        self, username: str, user: User
    ) -> dict:
        """Handle profile retrieval/creation for authenticated users"""
        # Check if user already has this profile
        profile_ids = [str(p.id) for p in user.profiles]  # type: ignore
        profiles = self.profile_repository.find_by_ids_and_username(
            profile_ids, username
        )
        if profiles:
            self.logger.debug(f"Profile already exists for user: {username}.")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=ApiErrorType.ResourceAlreadyExists.value,
            )

        # Otherwise, fetch from LinkedIn & transform
        profile = await self._fetch_and_transform_profile(
            username=username, is_authenticated=True, user_id=str(user.id)
        )

        # Persist to db
        profile = self.profile_repository.create(profile)

        # Link the profile to the user
        self.user_repository.append_profile_to_user(profile, user)
        self.logger.debug(f"Profile record created and linked to user for: {username}")

        profile = self.profile_repository.find_by_id(str(profile.id))
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Profile not found for username: {username}",
            )

        return profile.to_mongo().to_dict()

    @handle_exceptions()
    async def _create_guest_profile_from_remote_data(self, username: str) -> dict:
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
    async def create_profile_from_remote_data(
        self, link: str, user: Optional[User] = None
    ) -> dict:
        """Create a profile by username with data from data broker. Uses db as cache."""
        username = self._extract_username(link)
        self.logger.debug(f"Extracted username: {username}")

        is_authenticated = user is not None

        if is_authenticated:
            return await self._create_profile_for_user_from_remote_data(username, user)

        return await self._create_guest_profile_from_remote_data(username)

    @handle_exceptions()
    async def get_profile(self, username: str, user: Optional[User] = None) -> dict:
        """Get a profile by username from database"""
        if user:
            profile = await self._get_profile_from_user_by_username(username, user)
            if not profile:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=ApiErrorType.ResourceNotFound.value,
                )
            if not self._user_has_access_to_profile(user, profile):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=ApiErrorType.Forbidden.value,
                )

        else:
            profile = self.profile_cache_repository.find_by_username(username)
            if not profile:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=ApiErrorType.ResourceNotFound.value,
                )

        return profile.to_mongo().to_dict()

    @handle_exceptions()
    async def get_published_profiles(self) -> list[dict]:
        """Get all published profiles"""
        profiles = self.profile_repository.find_published_profiles()
        return [profile.to_mongo().to_dict() for profile in profiles]

    @handle_exceptions()
    async def get_published_profile(self, slug: str) -> dict:
        """Get a published profile"""
        profile = self.profile_repository.find_published_by_slug(slug)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ApiErrorType.ResourceNotFound.value,
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
            profile = await self._get_profile_from_user_by_username(username, user)
            if not profile:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=ApiErrorType.ResourceNotFound.value,
                )
            if not self._user_has_access_to_profile(user, profile):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=ApiErrorType.Forbidden.value,
                )

            updated_profile = self.profile_repository.update(profile, data_to_update)

        else:
            guest_profile = self.profile_cache_repository.find_by_username(username)

            if not guest_profile:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=ApiErrorType.ResourceNotFound.value,
                )

            updated_profile = self.profile_cache_repository.update(
                guest_profile, data_to_update
            )

        return updated_profile.to_mongo().to_dict()

    @handle_exceptions()
    async def delete_profile(self, username: str, user: User) -> None:
        """
        Delete a profile
        Only the owner of the profile can delete it
        """
        profile = await self._get_profile_from_user_by_username(username, user)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ApiErrorType.ResourceNotFound.value,
            )
        if not self._user_has_access_to_profile(user, profile):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=ApiErrorType.Forbidden.value,
            )

        await self.file_service.delete_files_from_folder(
            f"{user.id}/{profile.username}"
        )

        self.profile_repository.delete(profile)
        return None

    @handle_exceptions()
    async def publish_profile(
        self, username: str, data: PublishingOptionsUpdate, user: User
    ) -> dict:
        """
        Publish a profile
        """
        publishing_options = data.model_dump(
            mode="json",
            exclude_unset=True,
            exclude_none=True,
        )

        data_to_update = {
            "publishingOptions": publishing_options,
        }

        profile = await self._get_profile_from_user_by_username(username, user)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ApiErrorType.ResourceNotFound.value,
            )
        if not self._user_has_access_to_profile(user, profile):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=ApiErrorType.Forbidden.value,
            )

        await self._make_files_public(profile)

        try:
            updated_profile = self.profile_repository.update(profile, data_to_update)
            return updated_profile.to_mongo().to_dict()
        except Exception as exc:
            # Check for MongoDB duplicate key error (slug has to be unique)
            if "duplicate key error" in str(exc):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=ApiErrorType.ResourceAlreadyExists.value,
                )
            else:
                raise exc

    @handle_exceptions()
    async def unpublish_profile(self, username: str, user: User) -> dict:
        """
        Unpublish a profile
        """
        profile = await self._get_profile_from_user_by_username(username, user)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ApiErrorType.ResourceNotFound.value,
            )
        if not self._user_has_access_to_profile(user, profile):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=ApiErrorType.Forbidden.value,
            )

        await self.file_service.delete_public_files_from_folder(
            f"{user.id}/{profile.username}"
        )

        updated_profile = self.profile_repository.update(
            profile,
            {
                "publishingOptions": {},
            },
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
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ApiErrorType.ResourceNotFound.value,
            )

        self.logger.debug(f"Found guest profile for username: {username}")

        # Check if user already has this profile
        existing_profile = await self._get_profile_from_user_by_username(username, user)
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
        for profile_ref in user.profiles:  # type: ignore
            profile = self.profile_repository.find_by_id(str(profile_ref.id))
            if profile:
                profiles.append(profile.to_mongo().to_dict())

        return profiles
