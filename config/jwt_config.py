import os
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import Depends, HTTPException, status
from dotenv import load_dotenv
from datetime import datetime, timedelta
import jwt
from config import get_setting
from config.logger_config import logger
from model.jwt_model import TokenData
from router.auth import authentication
from fastapi.security import OAuth2PasswordBearer
from model.user_model import UserModel

load_dotenv()

client = AsyncIOMotorClient(get_setting().MONGODB_URI)
database = client.get_default_database()
black_listed_collection = database['blacklisted']


JWT_SECRET = os.getenv('JWT_SECRET')
JWT_ALGORITHM = os.getenv('JWT_ALGORITHM')
REFRESH_TOKEN_EXPIRE_DAYS = os.getenv('REFRESH_TOKEN_EXPIRE_DAYS')
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def create_access_token(session_id: str, data: dict):
    logger.info(f'[{session_id}] setting up access token')
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(15)
    to_encode.update({'exp': expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    logger.info(f'[{session_id}] done setting us access token')
    return encoded_jwt


def create_refresh_token(session_id: str, data: dict):
    logger.info(f'[{session_id}] setting up refresh id')
    expire = datetime.utcnow() + timedelta(days=int(REFRESH_TOKEN_EXPIRE_DAYS))
    to_encode = data.copy()
    to_encode.update({'exp': expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    logger.info(f'[{session_id}] done setting up refresh token')
    return encoded_jwt


async def get_current_user(session_id, token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not verify credentials',
        headers={'WWW-Authenticate': 'Bearer'}
    )
    try:
        logger.info(f'[{session_id}] checking blacklisted collection')
        black_list = await black_listed_collection.find_one({'token': token})
        if black_list:
            logger.info(f'[{session_id}] token found in blacklisted collection')
            raise HTTPException(
                status_code=401,
                detail='Token has been revoked'
            )
        logger.info(f'[{session_id}] token not blacklisted, about to fetch details')
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        username: str = payload.get('sub')
        if username is None:
            logger.info(f'[{session_id}] no username found')
            raise credentials_exception
        _ = TokenData(username=username)
    except jwt.PyJWTError:
        raise credentials_exception
    logger.info(f'[{session_id}] found user')
    user = await authentication.get_user(session_id, username)
    if user is None:
        logger.info(f'[{session_id}] wrong credentials')
        raise credentials_exception
    logger.info(f'[{session_id}] returning user')
    return user


async def get_current_active_user(current_user: UserModel = Depends(get_current_user)):
    if current_user.activated:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='User not activated')
