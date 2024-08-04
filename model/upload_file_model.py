from pydantic import BaseModel

class FileUploadModel(BaseModel):
    file: str
    file_name: str
    file_extention: str