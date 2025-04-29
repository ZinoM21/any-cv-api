import re
import time
import traceback
from typing import Any, Dict, Optional

from dateutil import parser as date_parser

from src.config import Settings
from src.core.domain.interfaces import IDataTransformer, IFileService, ILogger
from src.core.domain.models import (
    Education,
    Experience,
    Position,
    Profile,
    Project,
    VolunteeringExperience,
)


class DataTransformerError(Exception):
    """Base exception for DataTransformer errors."""

    pass


class DataValidationError(DataTransformerError):
    """Raised when data validation fails."""

    pass


class DataTransformer(IDataTransformer):
    """Transforms LinkedIn API data into domain model objects.

    This transformer handles data from a third-party API, performing validation,
    sanitization, and transformation into domain objects. It's designed to be
    resilient against missing fields, malformed data, and API changes.
    """

    def __init__(self, logger: ILogger, settings: Settings, file_service: IFileService):
        self.logger: ILogger = logger
        self.settings: Settings = settings
        self.file_service: IFileService = file_service

    def _safe_get(self, data: Dict[str, Any], key: str, default: Any = None) -> Any:
        """Safely retrieve a value from a dictionary, returning default if key doesn't exist."""
        return data.get(key, default)

    def _safe_extract_text(self, items: list[Dict[str, Any]]) -> str:
        """Safely extract text from a list of components."""
        if not items or not isinstance(items, list):
            return ""

        text_parts = []
        for item in items:
            if (
                isinstance(item, dict)
                and "text" in item
                and item.get("type") == "textComponent"
            ):
                text_parts.append(item["text"])
        return " ".join(text_parts)

    def _get_snake_case_file_name(self, starting_string: str) -> str:
        """Get a filename for an image URL."""
        # Convert to snake_case and append _logo
        sanitized = re.sub(r"[^a-zA-Z0-9]", "_", starting_string.lower())
        sanitized = re.sub(r"_+", "_", sanitized)
        return f"{sanitized.strip('_')}_logo"

    def __extract_date_info(self, caption: str) -> tuple:
        """Helper to extract start date, end date and duration from caption."""
        if not caption or not isinstance(caption, str):
            self.logger.warn(f"Invalid date caption: {caption}")
            return None, None, None

        try:
            date_parts = caption.split(" · ")
            dates = date_parts[0].split(" - ")
            start_date_str = dates[0].strip()
            end_date_str = dates[1].strip() if len(dates) > 1 else None

            # Use dateutil's parser which handles various date formats
            start_date = (
                date_parser.parse(start_date_str, fuzzy=True)
                if start_date_str
                else None
            )
            # If end date is "Present" or similar, set to None
            end_date = (
                None
                if not end_date_str or end_date_str.lower() in ["present", "current"]
                else date_parser.parse(end_date_str, fuzzy=True)
            )

            duration = date_parts[1] if len(date_parts) > 1 else None
            return start_date, end_date, duration
        except Exception as e:
            self.logger.warn(f"Error extracting date info from '{caption}': {str(e)}")
            return None, None, None

    def __extract_location_work_setting(self, metadata: str) -> tuple:
        """Helper to extract location and work setting from metadata."""
        if not metadata or not isinstance(metadata, str):
            return "", ""

        try:
            parts = metadata.split(" · ")
            location = parts[0].strip() if parts else ""
            work_setting = parts[1].strip() if len(parts) > 1 else ""
            return location, work_setting
        except Exception as e:
            self.logger.warn(
                f"Error extracting location and work setting from '{metadata}': {str(e)}"
            )
            return "", ""

    async def _process_profile_picture(
        self, data: dict, path_prefix: str, is_authenticated: bool = True
    ) -> str | None:
        """Process the profile picture URL."""
        all_profile_pics: list[dict[str, str]] = data.get("profilePicAllDimensions", [])
        profile_pic_url = data.get("profilePic", "")
        preferred_dimensions = [800, 400, 200, 100]

        if all_profile_pics:
            # Try to find profile pic with preferred dimensions in order of preference
            for width in preferred_dimensions:
                for pic in all_profile_pics:
                    if pic.get("width") == width and pic.get("url"):
                        profile_pic_url = pic.get("url")
                        break
                if profile_pic_url != data.get("profilePic", ""):
                    break

        profile_pic_path = (
            await self.file_service.download_and_store_file(
                profile_pic_url,
                path_prefix=path_prefix,
                filename="profile_picture",
            )
            if is_authenticated and profile_pic_url
            else profile_pic_url
        )
        self.logger.debug(f"Processed profile picture: {profile_pic_path}")

        return profile_pic_path

    async def __format_experience(
        self,
        exp: dict,
        path_prefix: str,
        is_authenticated: bool = True,
    ) -> Optional[Experience]:
        """Transforms raw experience data into an Experience object.

        Handles both single positions and multiple positions under one company.
        Returns None if critical data is missing or malformed.
        """
        if not exp or not isinstance(exp, dict):
            return None

        try:
            # Check for required fields
            if not exp.get("title"):
                self.logger.warn("Experience missing required title field")
                return None

            # Extract company name from title
            companyName = exp.get("title", "").strip()

            # Process company logo
            company_logo_url: str = exp.get("logo", "")
            processed_logo_url = (
                await self.file_service.download_and_store_file(
                    company_logo_url,
                    path_prefix=path_prefix,
                    filename=self._get_snake_case_file_name(companyName),
                )
                if is_authenticated
                else company_logo_url
            )

            # Handle experiences with multiple positions (breakdown=true)
            if exp.get("breakdown"):
                positions = []

                # For multiple positions, the shared location is in the experience's caption
                location, work_setting = self.__extract_location_work_setting(
                    exp.get("caption", "")
                )

                for pos in exp.get("subComponents", []):
                    if not pos.get("title"):  # Skip entries without title
                        continue

                    # For multiple positions, dates and duration are in the position's caption
                    start_date, end_date, duration = self.__extract_date_info(
                        pos.get("caption", "")
                    )

                    # Extract description from position's description field
                    description = ""
                    if isinstance(pos.get("description"), list):
                        for desc in pos.get("description", []):
                            if isinstance(desc, dict) and "text" in desc:
                                if (
                                    desc.get("type") == "textComponent"
                                    or desc.get("type") is None
                                ):
                                    description += desc.get("text", "") + " "

                    # Get additional role information from subtitle if available
                    role_subtitle = pos.get("subtitle", "")
                    full_title = pos.get("title", "")
                    if role_subtitle:
                        full_title = f"{full_title} ({role_subtitle})"

                    positions.append(
                        Position(
                            title=full_title,
                            startDate=start_date,
                            endDate=end_date,
                            duration=duration,
                            description=description.strip(),
                            location=location,
                            workSetting=work_setting,
                        )
                    )

                if not positions:  # Skip if no valid positions
                    return None

                return Experience(
                    company=companyName,
                    companyProfileUrl=exp.get("companyLink1", ""),
                    companyLogoUrl=processed_logo_url,
                    positions=positions,
                )
            else:
                # Handle single position experiences (breakdown=false)

                # For single positions, dates and duration are in the experience's caption
                start_date, end_date, duration = self.__extract_date_info(
                    exp.get("caption", "")
                )

                # For single positions, location and work setting are in the experience's metadata
                location, work_setting = self.__extract_location_work_setting(
                    exp.get("metadata", "")
                )

                # Extract the company name from subtitle (handle potential missing data)
                company = ""
                if exp.get("subtitle"):
                    subtitle_parts = exp.get("subtitle", "").split(" · ")
                    if subtitle_parts:
                        company = subtitle_parts[0].strip()

                description = ""
                for subc in exp.get("subComponents", []):
                    if isinstance(subc, dict):
                        for d in subc.get("description", []):
                            if (
                                isinstance(d, dict)
                                and "text" in d
                                and d.get("type") == "textComponent"
                            ):
                                description += d["text"] + " "

                return Experience(
                    company=company,
                    companyProfileUrl=exp.get("companyLink1", ""),
                    companyLogoUrl=processed_logo_url,
                    positions=[
                        Position(
                            title=exp["title"],
                            startDate=start_date,
                            endDate=end_date,
                            duration=duration,
                            description=description.strip(),
                            location=location,
                            workSetting=work_setting,
                        )
                    ],
                )
        except Exception as e:
            self.logger.error(
                f"Error formatting experience: {str(e)}\n{traceback.format_exc()}"
            )
            return None

    async def __format_education(
        self,
        edu: dict,
        path_prefix: str,
        is_authenticated: bool = True,
    ) -> Optional[Education]:
        """Transforms raw education data into an Education object.

        Returns None if critical data is missing or malformed.
        """
        if not edu or not isinstance(edu, dict):
            return None

        eduName = edu.get("title", "").strip()

        try:
            # Check for required fields
            if not edu.get("title"):
                self.logger.warn("Education missing required title field")
                return None

            # Process school logo
            school_logo_url: str = edu.get("logo", "")
            processed_logo_url = (
                await self.file_service.download_and_store_file(
                    school_logo_url,
                    path_prefix=path_prefix,
                    filename=self._get_snake_case_file_name(eduName),
                )
                if is_authenticated
                else school_logo_url
            )

            # Extract date info
            start_date, end_date, _ = self.__extract_date_info(edu.get("caption", ""))

            # Default values for degree components
            degree = ""
            field_of_study = None

            # Safely parse degree information
            if edu.get("subtitle"):
                degree_parts = edu["subtitle"].split(", ")
                degree = degree_parts[0] if degree_parts else ""
                field_of_study = degree_parts[1] if len(degree_parts) > 1 else None

            description_text = ""
            activities_text = ""
            grade_text = ""
            for subc in edu.get("subComponents", []):
                if not isinstance(subc, dict):
                    continue

                for desc in subc.get("description", []):
                    if isinstance(desc, dict):
                        if desc.get("type") == "textComponent":
                            description_text += desc.get("text", "") + " "
                        elif desc.get("type") == "insightComponent":
                            text = desc.get("text", "")
                            if text.startswith("Grade: "):
                                grade = text[len("Grade: ") :].strip()
                                grade_text = grade
                            elif text.startswith("Activities and societies: "):
                                activities_text += (
                                    text[len("Activities and societies: ") :].strip()
                                    + " "
                                )
                            else:
                                activities_text += text + " "

            return Education(
                school=eduName,
                schoolProfileUrl=edu.get("companyLink1", ""),
                schoolPictureUrl=processed_logo_url,
                degree=degree,
                fieldOfStudy=field_of_study,
                startDate=start_date,
                endDate=end_date,
                grade=grade_text.strip() or None,
                activities=activities_text.strip() or None,
                description=description_text.strip() or None,
            )

        except Exception as e:
            self.logger.error(
                f"Error formatting education: {str(e)}\n{traceback.format_exc()}"
            )
            return None

    async def __format_volunteering(
        self,
        vol: dict,
        path_prefix: str,
        is_authenticated: bool = True,
    ) -> Optional[VolunteeringExperience]:
        """Transforms raw volunteering data into a VolunteeringExperience object.

        Returns None if critical data is missing or malformed.
        """
        if not vol or not isinstance(vol, dict):
            return None

        try:
            # Check for required fields
            if not vol.get("title") or not vol.get("subtitle"):
                self.logger.warn(
                    "Volunteering missing required title or subtitle field"
                )
                return None

            orgName = vol.get("subtitle", "").strip()

            # Process organization logo
            org_logo_url: str = vol.get("logo", "")
            processed_logo_url = (
                await self.file_service.download_and_store_file(
                    org_logo_url,
                    path_prefix=path_prefix,
                    filename=self._get_snake_case_file_name(orgName),
                )
                if is_authenticated
                else org_logo_url
            )

            start_date, end_date, _ = self.__extract_date_info(vol.get("caption", ""))

            description = ""
            for subc in vol.get("subComponents", []):
                if isinstance(subc, dict):
                    for d in subc.get("description", []):
                        if isinstance(d, dict) and "text" in d:
                            description += d["text"] + " "

            return VolunteeringExperience(
                role=vol["title"],
                organization=orgName,
                organizationProfileUrl=vol.get("companyLink1", ""),
                organizationLogoUrl=processed_logo_url,
                cause=vol.get("metadata", ""),
                startDate=start_date,
                endDate=end_date,
                description=description.strip(),
            )

        except Exception as e:
            self.logger.error(
                f"Error formatting volunteering experience: {str(e)}\n{traceback.format_exc()}"
            )
            return None

    async def __format_project(
        self,
        project_data: dict,
        path_prefix: str,
        is_authenticated: bool = True,
    ) -> Optional[Project]:
        """Transforms raw project data into a Project object.

        Returns None if critical data is missing or malformed.
        """
        if not project_data or not isinstance(project_data, dict):
            return None

        projectName = project_data.get("title", "").strip()

        try:
            # Check for required fields
            if not project_data.get("title"):
                self.logger.warn("Project missing required title field")
                return None

            # Extract dates and duration from the subtitle field
            start_date, end_date, _ = self.__extract_date_info(
                project_data.get("subtitle", "")
            )

            description = ""
            associated_with = ""
            thumbnail_path = ""

            # Process sub-components for additional information
            for subc in project_data.get("subComponents", []):
                if isinstance(subc, dict):
                    for desc in subc.get("description", []):
                        if isinstance(desc, dict):
                            # Extract text description
                            if desc.get("type") == "textComponent" and "text" in desc:
                                description += desc["text"] + " "

                            # Extract association information
                            elif (
                                desc.get("type") == "insightComponent"
                                and "text" in desc
                            ):
                                insight_text = desc["text"]
                                if insight_text.startswith("Associated with"):
                                    associated_with = insight_text.replace(
                                        "Associated with", ""
                                    ).strip()

                            # Upload potential URL from media components
                            elif (
                                desc.get("type") == "mediaComponent"
                                and "thumbnail" in desc
                            ):
                                thumbnailUrl = desc.get("thumbnail", "")
                                thumbnail_path = (
                                    await self.file_service.download_and_store_file(
                                        thumbnailUrl,
                                        path_prefix=path_prefix,
                                        filename=self._get_snake_case_file_name(
                                            projectName
                                        ),
                                    )
                                    if is_authenticated
                                    else thumbnailUrl
                                )

            return Project(
                title=projectName,
                startDate=start_date,
                endDate=end_date,
                description=description.strip() or None,
                thumbnail=thumbnail_path or None,
                associatedWith=associated_with or None,
            )

        except Exception as e:
            self.logger.error(
                f"Error formatting project: {str(e)}\n{traceback.format_exc()}"
            )
            return None

    def __format_languages(self, languages_data: list[dict]) -> list[str]:
        """Transforms raw language data into a list of formatted language strings.

        Returns an empty list if no valid language entries are found.
        """
        formatted_languages = []
        if not languages_data or not isinstance(languages_data, list):
            return formatted_languages

        for lang in languages_data:
            try:
                if not isinstance(lang, dict) or not lang.get("title"):
                    continue

                language_name = lang.get("title", "").strip()
                proficiency = lang.get("caption", "").strip()

                if language_name:
                    if proficiency:
                        formatted_languages.append(f"{language_name} - {proficiency}")
                    else:
                        formatted_languages.append(language_name)
            except Exception as e:
                self.logger.warn(f"Error formatting language entry: {str(e)}")
                continue

        return formatted_languages

    async def transform_profile_data(
        self,
        data: dict,
        is_authenticated: bool = True,
        user_id: Optional[str] = None,
    ) -> Profile | None:
        """Transform LinkedIn API response to match frontend types.

        Implements retry logic for transient failures and comprehensive error handling.
        Validates and sanitizes the input data to ensure consistent output format.

        Args:
            data: The raw LinkedIn API response.
            is_authenticated: Whether the user is authenticated
            user_id: The ID of the authenticated user (if available)

        Returns:
            A Profile object containing the transformed data.

        Raises:
            DataValidationError: If the data is critically malformed.
            DataTransformerError: For other transformation errors.
        """
        retries = 0
        last_exception = None

        while retries < self.settings.EXTERNAL_MAX_RETRIES:
            try:
                # Validate the input data structure
                if not data or not isinstance(data, dict):
                    raise DataValidationError("Input data is null or not a dictionary")

                if "data" not in data:
                    raise DataValidationError("Input data missing 'data' field")

                linkedin_data = data["data"]
                if not linkedin_data or not isinstance(linkedin_data, dict):
                    raise DataValidationError(
                        "LinkedIn data is null or not a dictionary"
                    )

                # Check for required fields
                required_fields = ["publicIdentifier", "firstName", "lastName"]
                for field in required_fields:
                    if field not in linkedin_data:
                        raise DataValidationError(
                            f"Required field '{field}' is missing"
                        )

                username = linkedin_data.get("publicIdentifier", "")
                file_path_prefix = (user_id + "/" if user_id else "") + username

                # Extract and format language data from LinkedIn
                languages = self.__format_languages(linkedin_data.get("languages", []))

                # Process profile picture
                profile_pic_path = await self._process_profile_picture(
                    linkedin_data, file_path_prefix, is_authenticated
                )

                # Build profile data with safe defaults
                profile_data = {
                    "username": username,
                    "firstName": linkedin_data.get("firstName", ""),
                    "lastName": linkedin_data.get("lastName", ""),
                    "profilePictureUrl": profile_pic_path,
                    "jobTitle": linkedin_data.get("headline", ""),
                    "headline": linkedin_data.get("headline", ""),
                    "about": linkedin_data.get("about", ""),
                    "email": None,
                    "phone": None,
                    "website": (
                        linkedin_data.get("creatorWebsite", {}).get("link", "")
                        if isinstance(linkedin_data.get("creatorWebsite"), dict)
                        else ""
                    ),
                    "location": linkedin_data.get("addressWithCountry", ""),
                    "languages": languages,
                    "experiences": [
                        exp
                        for exp in [
                            await self.__format_experience(
                                exp,
                                path_prefix=file_path_prefix,
                                is_authenticated=is_authenticated,
                            )
                            for exp in linkedin_data.get("experiences", [])
                        ]
                        if exp is not None
                    ],
                    "education": [
                        edu
                        for edu in [
                            await self.__format_education(
                                edu,
                                path_prefix=file_path_prefix,
                                is_authenticated=is_authenticated,
                            )
                            for edu in linkedin_data.get("educations", [])
                        ]
                        if edu is not None
                    ],
                    "skills": [
                        skill.get("title", "")
                        for skill in linkedin_data.get("skills", [])
                        if isinstance(skill, dict) and skill.get("title")
                    ],
                    "volunteering": [
                        vol
                        for vol in [
                            await self.__format_volunteering(
                                vol,
                                path_prefix=file_path_prefix,
                                is_authenticated=is_authenticated,
                            )
                            for vol in linkedin_data.get("volunteerAndAwards", [])
                        ]
                        if vol is not None
                    ],
                    "projects": [
                        proj
                        for proj in [
                            await self.__format_project(
                                proj,
                                path_prefix=file_path_prefix,
                                is_authenticated=is_authenticated,
                            )
                            for proj in linkedin_data.get("projects", [])
                        ]
                        if proj is not None
                    ],
                }

                # Create and return the profile
                return Profile(**profile_data)

            except DataValidationError as e:
                # Don't retry validation errors - they're not transient
                self.logger.error(f"Data validation error: {str(e)}")
                raise

            except Exception as e:
                # Log the error and retry for other exceptions
                last_exception = e
                retries += 1
                self.logger.warn(
                    f"Error transforming profile data (attempt {retries}/{self.settings.EXTERNAL_MAX_RETRIES}): {str(e)}"
                )

                if retries < self.settings.EXTERNAL_MAX_RETRIES:
                    time.sleep(self.settings.EXTERNAL_RETRY_DELAY_SECONDS)
                else:
                    error_msg = f"Failed to transform profile data after {self.settings.EXTERNAL_MAX_RETRIES} attempts: {str(e)}"
                    self.logger.error(f"{error_msg}\n{traceback.format_exc()}")
                    raise DataTransformerError(error_msg) from last_exception
