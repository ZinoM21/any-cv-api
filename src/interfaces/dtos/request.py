from pydantic import BaseModel

class ProfileInfoRequest(BaseModel):
    link: str
