import os

from fastapi import HTTPException, APIRouter, status, Depends
from starlette.requests import Request
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from config.jwt_config import get_current_user, black_listed_collection, oauth2_scheme
from model.user_model import CreateUserModel, UserResponseModel, ResetPasswordModel, UserModel, LoginModel
from fastapi.security import OAuth2PasswordRequestForm
from config import get_setting
from config.jwt_config import create_access_token, create_refresh_token
from model.jwt_model import RefreshToken
from config.logger_config import logger
from util import mail_sender_utility
import uuid

router = APIRouter()

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

client = AsyncIOMotorClient(get_setting().MONGODB_URI)
database = client.get_default_database()

user_collection = database['users']
RAPID_API_KEY = os.getenv('RAPID_API_KEY')


async def get_user(session_id: str, username: str):
    logger.info(f'[{session_id}] about to find user from database')
    user = await user_collection.find_one({'username': {'$regex': f'^{username}$', '$options': 'i'}})
    logger.info(f'[{session_id}] user details-- {user}')
    if user is None:
        logger.info(f'[{session_id}] no username found')
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')
    logger.info(f'[{session_id}] done retrieving user')
    return UserModel(**user)


async def authenticate_user(session_id: str, username: str, password: str):
    logger.info(f'[{session_id}] about to authenticate user {username}')
    user = await get_user(session_id, username)
    
    if user is None:
        logger.info(f'[{session_id}] user {username} not found')
        return None
    
    if not verify_password(session_id, password, user.password):
        logger.info(f'[{session_id}] incorrect password for user {username}')
        return None
    
    if not user.activated:
        logger.info(f'[{session_id}] user {username} account not activated')
        return None
    
    logger.info(f'[{session_id}] user {username} authenticated successfully')
    return user


@router.post('/register', response_model=UserResponseModel, status_code=status.HTTP_201_CREATED)
async def create_user(user: CreateUserModel, request: Request):
    session_id = request.state.session_id
    if user.password != user.confirm_password:
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail='Passwords do not much'
        )
    user_dict = user.dict(exclude={'confirm_password'})
    user_dict['activated'] = False
    logger.info(f'[{session_id}] received request to create account')
    user_email = await user_collection.find_one({'email': user.email})
    username = await user_collection.find_one({'username': user.username})
    logger.info(f'[{session_id}] done checking if username or email already exits')

    if user_email or username:
        logger.info(f'[{session_id}] username or email already exists')
        raise HTTPException(status_code=400, detail='Username or Email already exists')

    if user.username[:2] == 'AD' and user.username[-2:] == 'MN':
        user_dict['ROLE'] = 'ADMIN'
    else:
        user_dict['ROLE'] = 'USER'

    logger.info(f'{session_id} username or email not found, about to attempting to create account')
    user_dict['password'] = pwd_context.hash(user.password)
    logger.info(f'[{session_id}] done hashing password')
    logger.info(f'[{session_id}] inserting details to database')
    # insert otp
    user_otp = str(uuid.uuid4())[:5]  # take 5 characters of the generated uuid
    user_dict['otp'] = user_otp
    # send mail to user
    content = f'''
    <h1 style="background-color: #add8e6; color: white; padding: 10px; display: inline-block">
        Your Account Verification Code
    </h1>
    <p>Use this code to verify your account: {user_otp}</p>
    <p><em>Regards,</em></p>
    <p><em>T2TB Team</em></p>
    '''
    logger.info(f'[{session_id}] about to send Otp to user mail')
    email_sender_response = await mail_sender_utility.send_email(user.email, 'Account Verification',
                                                                 content)
    if email_sender_response != 'success':
        raise HTTPException(
            status_code=500,
            detail='Error sending mail'
        )
    result = await user_collection.insert_one(user_dict)
    if result.inserted_id:
        logger.info(f'[{session_id}] done inserting user')
        return UserResponseModel(username=user.username, email=user.email, activated=False)
    logger.info(f'[{session_id}] error inserting user details to database')
    raise HTTPException(status_code=400, detail="Error creating account, try again later")


def verify_password(session_id: str, plain_password: str, hashed_password: str):
    logger.info(f'[{session_id}] about to verify password')
    return pwd_context.verify(plain_password, hashed_password)


@router.post('/login')
async def log_in(request: Request, form_data: LoginModel):
    session_id = request.state.session_id
    logger.info(f'[{session_id}] received login request, about to authenticate')
    
    user = await authenticate_user(session_id, form_data.username, form_data.password)
    
    if not user:
        logger.info(f'[{session_id}] authentication failed for user {form_data.username}')
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password or account not activated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    logger.info(f'[{session_id}] user {form_data.username} authenticated, generating access token')
    access_token = create_access_token(session_id, data={'sub': user.username})
    refresh_token = create_refresh_token(session_id, data={'sub': user.username})
    
    logger.info(f'[{session_id}] done generating tokens for user {form_data.username}')
    return {
        'username': user.username,
        'ROLE': user.ROLE,
        'access-token': access_token,
        'refresh-token': refresh_token,
        'token-type': 'Bearer'
    }


@router.post('/refresh')
async def refresh(httpRequest: Request, request: RefreshToken):
    session_id = httpRequest.state.session_id
    try:
        logger.info(f'[{session_id}] received request to refresh token, trying')
        user = await get_current_user(httpRequest, token=request.refresh_token)
        username: str = user.username
        logger.info(f'[{session_id}] returning username for refresh token')
    except HTTPException:
        logger.info(f'[{session_id}] token not valid')
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid Token')

    logger.info(f'[{session_id}] starting to create refresh token')
    new_access_token = create_access_token(session_id, data={'sub': username})
    new_refresh_token = create_refresh_token(session_id, data={'sub': username})
    logger.info(f'[{session_id}] done with refresh token')
    return {'username': username, 'access-token': new_access_token, 'refresh-token': new_refresh_token,
            'token-type': 'Bearer'}


@router.post('/logout')
async def logout(request: Request, token: str = Depends(oauth2_scheme)):
    session_id = request.state.session_id
    logger.info(f'[{session_id}] received request to log user out, adding token to blacklist')
    black_listed_collection.insert_one({'token': token})
    logger.info(f'[{session_id}] done blacklisting token, logout successful')
    return {'message': 'Logout success'}


@router.post('/confirm-account/{user_otp}', status_code=status.HTTP_202_ACCEPTED)
async def confirm_otp(user_otp: str):
    user = await user_collection.find_one({'otp': user_otp})
    if user is None:
        raise HTTPException(
            status_code=400, detail='User not found'
        )
    if user.get('activated') is True:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='User already activated'
        )
    await user_collection.find_one_and_update({'otp': user_otp}, {'$set': {'activated': True}})
    return {'success': 'user activated'}


@router.get('/reset-password')
async def reset_password(email: str):
    # get email from database
    user = await user_collection.find_one({'email': email})
    if user is None:
        raise HTTPException(
            status_code=404, detail='User not found'
        )
    # send otp to mail
    user_otp = str(uuid.uuid4())[:5]
    content = f'''
        <h1 style="background-color: #add8e6; color: white; padding: 10px; display: inline-block">
            Your Password Reset code
        </h1>
        <p>Use this code to reset your password: {user_otp}</p>
        <p><em>Regards,</em></p>
        <p><em>T2TB Team</em></p>
        '''

    email_sender_response = await mail_sender_utility.send_email(email, 'Password Reset', content)
    if email_sender_response == 'success':
        await user_collection.find_one_and_update({'email': email}, {'$set': {'otp': user_otp}})
        return {'message': 'Password reset otp sent'}
    else:
        HTTPException(
            status_code=500, detail='Sending mail failed, try again later'
        )



@router.patch('/reset/{user_otp}', status_code=status.HTTP_202_ACCEPTED)
async def confirm_and_reset_password(user_otp: str, request: Request, password_reset: ResetPasswordModel):
    session_id = request.state.session_id
    logger.info(f'[{session_id}] request recieved to reset user password')
    logger.info(f'[{session_id}] about to query for user with otp {user_otp}')

    user = await user_collection.find_one({'otp': user_otp})
    if user is None:
        logger.info(f'[{session_id}] No user with otp {user_otp} found')
        return HTTPException(
            status_code=404, detail='User not found'
        )
    logger.info(f'[{session_id}] user found, about to change password')
    if password_reset.password != password_reset.confirm_password:
        logger.info(f'[{session_id}] Passwords do not match')

        return HTTPException(
            status_code=409, detail='Passwords do not match'
        )
    logger.info(f'[{session_id}] Hashing password to save in database')
    hashed_password = pwd_context.hash(password_reset.password)
    logger.info(f'[{session_id}] creating access token for user')
    access_token = create_access_token(session_id, data={'sub': user.get('username')})
    refresh_token = create_refresh_token(session_id, data={'sub': user.get('username')})
    try:
        await user_collection.find_one_and_update({'user_otp': user_otp}, {'$set': {'password': hashed_password}})
        logger.info(f'[{session_id}] Done inserting data, returing user')
        return {
            'username': user.get('username'),
            'ROLE': user.get('ROLE'),
            'access-token': access_token,
            'refresh-token': refresh_token,
            'token-type': 'Bearer'
    }
    except Exception:
        return HTTPException(status_code=500, detail='Error updating password')
