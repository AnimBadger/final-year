from pydantic import BaseModel, EmailStr, validator
from typing import Optional


class CreateUserModel(BaseModel):
    username: str
    email: EmailStr
    password: str
    confirm_password: str
    institution: Optional[str] = None

    @validator('password')
    def validate_password(cls, value: str) -> str:
        if len(value) < 6:
            raise ValueError('Password must be at least 6 characters long')
        if not any(char.isdigit() for char in value):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isupper() for char in value):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(char.islower() for char in value):
            raise ValueError('Password must contain at least one lowercase letter')
        return value


class UserResponseModel(BaseModel):
    email: EmailStr
    username: str
    activated: bool


class ResetPasswordModel(BaseModel):
    password: str
    confirm_password: str

    @validator('password')
    def validate_password(cls, value: str) -> str:
        if len(value) < 6:
            raise ValueError('Password must be at least 6 characters long')
        if not any(char.isdigit() for char in value):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isupper() for char in value):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(char.islower() for char in value):
            raise ValueError('Password must contain at least one lowercase letter')
        return value



class UserModel(BaseModel):
    username: str
    email: EmailStr
    password: str
    institution: Optional[str] = None
    otp: Optional[str] = None
    ROLE: str = 'USER'
    activated: bool = False


class LoginModel(BaseModel):
    username: str
    password: str
