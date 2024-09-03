from pydantic import BaseModel, validator


class CommentModel(BaseModel):
    audio_id: str
    comment: str
    rating: int

    @validator('comment')
    def validate_comment(cls, value: str):
        if len(value) < 10:
            raise ValueError('Message is too short')
        return value
