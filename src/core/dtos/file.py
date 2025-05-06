from typing import List

from pydantic import BaseModel, InstanceOf


class SignedUploadUrlRequest(BaseModel):
    file_name: str
    file_type: str
    file_size: int
    public: bool = False


class SignedUrlRequest(BaseModel):
    file_path: str


class SignedUrlsRequest(BaseModel):
    file_paths: List[InstanceOf[str]]


class File(BaseModel):
    data: bytes
    filename: str
    mimetype: str


class SignedUrl(BaseModel):
    url: str
    path: str
