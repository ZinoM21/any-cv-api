from pydantic import BaseModel


class ImageDownload(BaseModel):
    data: bytes
    filename: str
    mimetype: str


class SignedUrl(BaseModel):
    signed_url: str
    path: str
