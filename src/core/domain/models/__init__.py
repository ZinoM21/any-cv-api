from .guest_profile import GuestProfile
from .profile import (
    Education,
    Experience,
    Position,
    Profile,
    Project,
    UpdateProfile,
    VolunteeringExperience,
)
from .user import User

# All models to instantiate on load
__beanie_models__ = [Profile, User, GuestProfile]

__all__ = ["Profile", "User", "GuestProfile"]
