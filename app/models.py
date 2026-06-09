from pydantic import BaseModel

class ReportPostRequest(BaseModel):
    reporter:str
    postId: str
    content: str

class ModerationResponse(BaseModel):
    postId: str
    message: str
