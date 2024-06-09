from pydantic import BaseModel


class UploadResponseModel(BaseModel):
    file_id: str
    message: str
