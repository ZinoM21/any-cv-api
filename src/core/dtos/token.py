from pydantic import BaseModel


class TokensResponse(BaseModel):
    access: str
    refresh: str


class RefreshRequest(BaseModel):
    refresh_token: str


class AccessResponse(BaseModel):
    access: str
