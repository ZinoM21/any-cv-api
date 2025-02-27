"""LinkedIn data transformation utilities."""

from models import Position, Experience, Education, VolunteeringExperience, Profile


def extract_date_info(caption: str) -> tuple:
    """Helper to extract start date, end date and duration from caption."""
    date_parts = caption.split(" · ")
    dates = date_parts[0].split(" - ")
    start_date = dates[0].strip()
    end_date = dates[1].strip() if len(dates) > 1 else None
    duration = date_parts[1] if len(date_parts) > 1 else None
    return start_date, end_date, duration


def extract_location_work_setting(metadata: str) -> tuple:
    """Helper to extract location and work setting from metadata."""
    parts = metadata.split(" · ")
    location = parts[0].strip()
    work_setting = parts[1].strip() if len(parts) > 1 else None
    return location, work_setting


def format_experience(exp: dict) -> Experience:
    if exp.get("breakdown"):
        positions = []
        for pos in exp.get("subComponents", []):
            if not pos.get("title"):  # Skip entries without title
                continue
            start_date, end_date, duration = extract_date_info(pos.get("caption", ""))
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
        start_date, end_date, duration = extract_date_info(exp.get("caption", ""))
        location, work_setting = extract_location_work_setting(exp.get("metadata", ""))
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


def format_education(edu: dict) -> Education:
    start_date, end_date, _ = extract_date_info(edu.get("caption", ""))
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


def format_volunteering(vol: dict) -> VolunteeringExperience:
    start_date, end_date, _ = extract_date_info(vol.get("caption", ""))
    return VolunteeringExperience(
        role=vol["title"],
        organization=vol["subtitle"],
        organizationProfileUrl=vol.get("companyLink1"),
        Cause=vol.get("metadata", ""),
        startDate=start_date,
        endDate=end_date,
        description=" ".join(
            d["text"]
            for subc in vol.get("subComponents", [])
            for d in subc.get("description", [])
            if isinstance(d, dict) and "text" in d
        ),
    )


def create_profile_from_linkedin_data(data: dict) -> Profile:
    """Transform LinkedIn API response to match frontend types."""
    linkedin_data = data["data"]

    return Profile(
        username=linkedin_data["publicIdentifier"],
        firstName=linkedin_data["firstName"],
        lastName=linkedin_data["lastName"],
        profilePictureUrl=linkedin_data["profilePic"],
        jobTitle=linkedin_data["headline"],
        headline=linkedin_data["headline"],
        about=linkedin_data["about"],
        experiences=[format_experience(exp) for exp in linkedin_data["experiences"]],
        education=[format_education(edu) for edu in linkedin_data["educations"]],
        skills=[skill["title"] for skill in linkedin_data["skills"]],
        volunteering=[
            format_volunteering(vol) for vol in linkedin_data["volunteerAndAwards"]
        ],
    )
