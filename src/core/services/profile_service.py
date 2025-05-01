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
from src.core.domain.models import (
    GuestProfile,
    Profile,
    User,
)
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

    def extract_username(self, link: str) -> str:
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
                detail=ApiErrorType.InternalServerError.value,
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

    def _get_snake_case_file_name(self, starting_string: str) -> str:
        """Get a filename for an image URL."""
        # Convert to snake_case and append _logo
        sanitized = re.sub(r"[^a-zA-Z0-9]", "_", starting_string.lower())
        sanitized = re.sub(r"_+", "_", sanitized)
        return f"{sanitized.strip('_')}_logo"

    @handle_exceptions()
    def _get_all_profile_files(self, profile: Profile) -> dict[str, str]:
        """Get all files associated with a profile as a dictionary of name to file URL"""
        all_files: dict[str, str] = {}

        if profile.profilePictureUrl:  # type: ignore
            all_files["profilePicture"] = profile.profilePictureUrl  # type: ignore

        for exp in profile.experiences:  # type: ignore
            if exp.companyLogoUrl:
                company_name = exp.company if hasattr(exp, "company") else "company"
                all_files[company_name] = exp.companyLogoUrl

        for edu in profile.education:  # type: ignore
            if edu.schoolPictureUrl:
                school_name = edu.school if hasattr(edu, "school") else "school"
                all_files[school_name] = edu.schoolPictureUrl

        for vol in profile.volunteering:  # type: ignore
            if vol.organizationLogoUrl:
                org_name = (
                    vol.organization if hasattr(vol, "organization") else "organization"
                )
                all_files[org_name] = vol.organizationLogoUrl

        for proj in profile.projects:  # type: ignore
            if proj.thumbnail:
                proj_name = proj.title if hasattr(proj, "title") else "project"
                all_files[proj_name] = proj.thumbnail

        return {k: v for k, v in all_files.items() if v}

    @handle_exceptions()
    async def _make_files_public(self, profile: Profile) -> None:
        """Make files public"""
        self.logger.debug(f"Making files public for profile: {profile.username}")
        all_files: dict[str, str] = self._get_all_profile_files(profile)

        for _, file_path in all_files.items():
            if file_path:
                self.logger.debug(f"Copying file to public: {file_path}")
                await self.file_service.copy_files_from_private_to_public(file_path)

    @handle_exceptions()
    async def _upload_all_profile_files(
        self, profile: Profile, path_prefix: str
    ) -> dict[str, str]:
        """Upload all files from a profile to storage and return a mapping of old URLs to new file paths

        Args:
            profile: The profile to upload files from
            path_prefix: The prefix to use for the file paths (i.e. user_id/username)

        Returns:
            dict[str, str]: A dictionary mapping old URLs to new file paths
        """
        self.logger.debug(f"Uploading files from guest profile: {profile.username}")
        all_files: dict[str, str] = self._get_all_profile_files(profile)
        new_paths: dict[str, str] = {}

        for file_name, file_url in all_files.items():
            if file_url:
                self.logger.debug(f"Storing file: {file_name} for url: {file_url}")
                new_path = await self.file_service.download_and_store_file(
                    url=file_url,
                    path_prefix=path_prefix,
                    filename=self._get_snake_case_file_name(file_name),
                )
                if new_path:
                    new_paths[file_url] = new_path

        return new_paths

    @handle_exceptions()
    async def create_profile_for_user_from_remote_data(
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
    async def create_guest_profile_from_remote_data(self, username: str) -> dict:
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
            website=profile.website,
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

        # Delete from db first to cache errors before deleting files
        self.profile_repository.delete(profile)

        # Then delete files
        await self.file_service.delete_files_from_folder(
            f"{user.id}/{profile.username}"
        )

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

        try:
            updated_profile = self.profile_repository.update(profile, data_to_update)
            await self._make_files_public(profile)
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
    async def _update_profile_with_new_file_paths(
        self, profile: Profile, new_file_paths: dict[str, str]
    ) -> Profile:
        """
        Update a profile with new file paths and return the updated profile.

        Args:
            profile: The profile to update
            new_file_paths: A dictionary mapping old URLs to new file paths

        Returns:
            Profile: The updated profile or the original profile if no updates were made
        """
        update_data = {}
        # Update profile picture
        if profile.profilePictureUrl:
            if str(profile.profilePictureUrl) in new_file_paths:
                update_data["profilePictureUrl"] = new_file_paths[
                    str(profile.profilePictureUrl)
                ]

        # Update experience company logos
        if profile.experiences:
            experiences_data = []
            for exp in profile.experiences:  # type: ignore
                exp_data = exp.to_mongo().to_dict()
                if exp.companyLogoUrl:
                    if str(exp.companyLogoUrl) in new_file_paths:
                        exp_data["companyLogoUrl"] = new_file_paths[
                            str(exp.companyLogoUrl)
                        ]
                experiences_data.append(exp_data)
            update_data["experiences"] = experiences_data

        # Update education school pictures
        if profile.education:
            education_data = []
            for edu in profile.education:  # type: ignore
                edu_data = edu.to_mongo().to_dict()
                if edu.schoolPictureUrl:
                    if str(edu.schoolPictureUrl) in new_file_paths:
                        edu_data["schoolPictureUrl"] = new_file_paths[
                            str(edu.schoolPictureUrl)
                        ]
                education_data.append(edu_data)
            update_data["education"] = education_data

        # Update volunteering organization logos
        if profile.volunteering:
            volunteering_data = []
            for vol in profile.volunteering:  # type: ignore
                vol_data = vol.to_mongo().to_dict()
                if vol.organizationLogoUrl:
                    if str(vol.organizationLogoUrl) in new_file_paths:
                        vol_data["organizationLogoUrl"] = new_file_paths[
                            str(vol.organizationLogoUrl)
                        ]
                volunteering_data.append(vol_data)
            update_data["volunteering"] = volunteering_data

        # Update project thumbnails
        if profile.projects:
            projects_data = []
            for proj in profile.projects:  # type: ignore
                proj_data = proj.to_mongo().to_dict()
                if proj.thumbnail:
                    if str(proj.thumbnail) in new_file_paths:
                        proj_data["thumbnail"] = new_file_paths[str(proj.thumbnail)]
                projects_data.append(proj_data)
            update_data["projects"] = projects_data

        # Save the updated profile
        if update_data:
            return self.profile_repository.update(profile, update_data)
        return profile

    @handle_exceptions()
    async def transfer_guest_profile_to_user(self, username: str, user: User) -> dict:
        """
        Transfer a guest profile to a user profile after sign-in.
        1. Find the guest profile
        2. Create a new Profile entry
        3. Download & store all files.
        4. Link it to the user
        5. Delete the guest profile
        6. Return the new profile
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
            website=guest_profile.website,
            location=guest_profile.location,
            languages=guest_profile.languages,
            experiences=guest_profile.experiences,
            education=guest_profile.education,
            skills=guest_profile.skills,
            volunteering=guest_profile.volunteering,
            projects=guest_profile.projects,
        )
        profile = self.profile_repository.create(new_profile)

        # Upload all files from guest profile to storage and get new paths
        path_prefix = str(user.id) + "/" + username
        new_file_paths = await self._upload_all_profile_files(profile, path_prefix)

        # Update profile with new file paths
        if new_file_paths:
            profile = await self._update_profile_with_new_file_paths(
                profile, new_file_paths
            )

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
