from pydantic import BaseModel


class File(BaseModel):
    data: bytes
    filename: str
    mimetype: str


class SignedUrl(BaseModel):
    url: str
    path: str
