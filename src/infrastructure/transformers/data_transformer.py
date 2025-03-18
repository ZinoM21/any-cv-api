from datetime import datetime

from src.core.domain.interfaces import IDataTransformer
from src.core.domain.interfaces.logger_interface import ILogger
from src.core.domain.models.profile import (
    Education,
    Experience,
    Position,
    Profile,
    VolunteeringExperience,
)


class DataTransformer(IDataTransformer):
    def __init__(self, logger):
        self.logger: ILogger = logger

    def __extract_date_info(self, caption: str) -> tuple:
        """Helper to extract start date, end date and duration from caption."""
        try:
            date_parts = caption.split(" · ")
            dates = date_parts[0].split(" - ")
            start_date_str = dates[0].strip()
            end_date_str = dates[1].strip() if len(dates) > 1 else None

            start_date = datetime.fromisoformat(start_date_str)
            # If end date is "Present" or similar, set to None
            end_date = (
                None
                if not end_date_str or end_date_str.lower() in ["present", "current"]
                else datetime.fromisoformat(end_date_str)
            )

            duration = date_parts[1] if len(date_parts) > 1 else None
            return start_date, end_date, duration
        except Exception as e:
            raise ValueError(f"Error extracting date info: {str(e)}")

    def __extract_location_work_setting(self, metadata: str) -> tuple:
        """Helper to extract location and work setting from metadata."""
        try:
            parts = metadata.split(" · ")
            location = parts[0].strip()
            work_setting = parts[1].strip() if len(parts) > 1 else None
            return location, work_setting
        except Exception as e:
            raise ValueError(f"Error extracting location and work setting: {str(e)}")

    def __format_experience(self, exp: dict) -> Experience:
        try:
            if exp.get("breakdown"):
                positions = []
                for pos in exp.get("subComponents", []):
                    if not pos.get("title"):  # Skip entries without title
                        continue
                    start_date, end_date, duration = self.__extract_date_info(
                        pos.get("caption", "")
                    )
                    positions.append(
                        Position(
                            title=pos["title"],
                            startDate=start_date,
                            endDate=end_date,
                            duration=duration,
                            description=" ".join(
                                d["text"]
                                for d in pos.get("description", [])
                                if isinstance(d, dict)
                                and "text" in d
                                and d.get("type") == "textComponent"
                            ),
                            location=exp.get("caption"),
                            workSetting=pos.get("metadata"),
                        )
                    )
                return Experience(
                    company=exp["title"],
                    companyProfileUrl=exp.get("companyLink1"),
                    companyLogoUrl=exp.get("logo"),
                    positions=positions,
                )
            else:
                start_date, end_date, duration = self.__extract_date_info(
                    exp.get("caption", "")
                )
                location, work_setting = self.__extract_location_work_setting(
                    exp.get("metadata", "")
                )
                return Experience(
                    company=exp.get("subtitle", "").split(" · ")[0],
                    companyProfileUrl=exp.get("companyLink1"),
                    companyLogoUrl=exp.get("logo"),
                    positions=[
                        Position(
                            title=exp["title"],
                            startDate=start_date,
                            endDate=end_date,
                            duration=duration,
                            description=" ".join(
                                d["text"]
                                for subc in exp.get("subComponents", [])
                                for d in subc.get("description", [])
                                if isinstance(d, dict)
                                and "text" in d
                                and d.get("type") == "textComponent"
                            ),
                            location=location,
                            workSetting=work_setting,
                        )
                    ],
                )
        except Exception as e:
            raise ValueError(f"Error formatting experience: {str(e)}")

    def __format_education(self, edu: dict) -> Education:
        try:
            start_date, end_date, _ = self.__extract_date_info(edu.get("caption", ""))
            degree_parts = edu["subtitle"].split(", ")

            description_text = ""
            activities_text = ""

            for subc in edu.get("subComponents", []):
                for desc in subc.get("description", []):
                    if isinstance(desc, dict):
                        if desc.get("type") == "textComponent":
                            description_text += desc.get("text", "") + " "
                        elif desc.get("type") == "insightComponent":
                            activities_text += desc.get("text", "") + " "

            return Education(
                school=edu["title"],
                schoolProfileUrl=edu.get("companyLink1"),
                schoolPictureUrl=edu.get("logo"),
                degree=degree_parts[0],
                fieldOfStudy=degree_parts[1] if len(degree_parts) > 1 else None,
                startDate=start_date,
                endDate=end_date,
                activities=activities_text.strip() or None,
                description=description_text.strip() or None,
            )

        except Exception as e:
            raise ValueError(f"Error formatting education: {str(e)}")

    def __format_volunteering(self, vol: dict) -> VolunteeringExperience:
        try:
            start_date, end_date, _ = self.__extract_date_info(vol.get("caption", ""))
            return VolunteeringExperience(
                role=vol["title"],
                organization=vol["subtitle"],
                organizationProfileUrl=vol.get("companyLink1"),
                organizationLogoUrl=vol.get("logo"),
                cause=vol.get("metadata", ""),
                startDate=start_date,
                endDate=end_date,
                description=" ".join(
                    d["text"]
                    for subc in vol.get("subComponents", [])
                    for d in subc.get("description", [])
                    if isinstance(d, dict) and "text" in d
                ),
            )

        except Exception as e:
            raise ValueError(f"Error formatting volunteering experience: {str(e)}")

    def transform_profile_data(self, data: dict) -> Profile:
        """Transform LinkedIn API response to match frontend types."""
        try:
            linkedin_data = data["data"]

            profile_data = {
                "username": linkedin_data["publicIdentifier"],
                "firstName": linkedin_data["firstName"],
                "lastName": linkedin_data["lastName"],
                "profilePictureUrl": linkedin_data["profilePic"],
                "jobTitle": linkedin_data["headline"],
                "headline": linkedin_data["headline"],
                "about": linkedin_data["about"],
                "experiences": [
                    self.__format_experience(exp)
                    for exp in linkedin_data["experiences"]
                ],
                "education": [
                    self.__format_education(edu) for edu in linkedin_data["educations"]
                ],
                "skills": [skill["title"] for skill in linkedin_data["skills"]],
                "volunteering": [
                    self.__format_volunteering(vol)
                    for vol in linkedin_data["volunteerAndAwards"]
                ],
            }

            return Profile(**profile_data)

        except Exception as e:
            raise ValueError(f"Error transforming profile data: {str(e)}")
