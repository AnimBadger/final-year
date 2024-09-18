import base64
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorClient
from config import get_setting
from config.jwt_config import get_current_user
from model.jwt_model import TokenData
from router.auth.authentication import user_collection
from router.base.base_txt_to_twi import comments_collection
from provider.twi_to_audio_api import audio_files_collection

router = APIRouter()
client = AsyncIOMotorClient(get_setting().MONGODB_URI)
database = client.get_default_database()


@router.get('/get-comments')
async def get_comments(token: TokenData = Depends(get_current_user)):
    admin_user = await user_collection.find_one({'username': token.username, 'ROLE': 'ADMIN'})
    if admin_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail='Insufficient privileges'
        )
    
    comments_cursor = comments_collection.find().sort('created_at', -1)
    files = await comments_cursor.to_list(length=None)
    comments_list = []
    
    for data in files:
        audio_id = data['audio_id']
        # Fetch the audio file from the audio_files collection
        audio_file_data = await audio_files_collection.find_one({'audio_id': audio_id})
        if audio_file_data:
            # base64 encoding
            base64_audio = base64.b64encode(audio_file_data['file']).decode('utf-8')
        else:
            base64_audio = None 

        comment_data = {
            'audio_id': audio_id,
            'audio_file': base64_audio,
            'created_by': data['user'],
            'comment': data['comment'],
            'created_at': data['created_at'],
            'rating': data['rating']
        }
        comments_list.append(comment_data)

    return comments_list
