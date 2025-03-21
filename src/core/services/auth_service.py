from fastapi import HTTPException, status
from passlib.context import CryptContext

from src.core.domain.interfaces import IAuthService, ILogger, IUserRepository
from src.core.domain.models.user import User, UserCreate, UserLogin, UserResponse



class AuthService(IAuthService):
    def __init__(
        self,
        user_repository: IUserRepository,
        logger: ILogger,
    ):
        self.user_repository = user_repository
        self.logger = logger
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        return self.pwd_context.hash(password)


    async def authenticate_user(self, user_data: UserLogin) -> UserResponse:
        user = await self.user_repository.find_by_email(user_data.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No user with this email",
            )

        if not self.verify_password(user_data.password, user.pw_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect password",
            )

        user_response = user.model_dump(exclude={"pw_hash"})
        return UserResponse(**user_response)


    async def register_user(self, user_data: UserCreate) -> UserResponse:
        existing_username = await self.user_repository.find_by_username(
            user_data.username
        )
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered",
            )

        existing_email = await self.user_repository.find_by_email(user_data.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        hashed_password = self.get_password_hash(user_data.password)

        new_user = await self.user_repository.create(
            User(
                pw_hash=hashed_password,
                **user_data.model_dump(exclude={"password"}),
            )
        )

        user_response = new_user.model_dump(exclude={"pw_hash"})
        return UserResponse(**user_response)
