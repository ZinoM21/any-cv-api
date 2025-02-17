from pydantic import BaseModel

class CVRequest(BaseModel):
    link: str
