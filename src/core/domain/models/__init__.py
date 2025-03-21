from .profile import Profile, UpdateProfile
from .user import User, UserCreate, UserUpdate

# All models to instantiate on load
__beanie_models__ = [Profile, User]
