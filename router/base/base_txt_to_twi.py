import io
from fastapi.responses import JSONResponse, StreamingResponse
import base64
from fastapi import APIRouter, HTTPException, status, Depends, Request
from motor.motor_asyncio import AsyncIOMotorClient
from config import get_setting
from model.upload_file_model import FileUploadModel
from model.download_audio_model import CommentModel
import uuid
from config.logger_config import logger
from config.jwt_config import get_current_user
from model.jwt_model import TokenData
from datetime import datetime, timezone
from converter import (docx_to_text_converter,
                       doc_to_text_conveter,
                       pdf_to_text_converter,
                       txt_to_text_conveter
                       )
from provider import summary_api, text_to_twi_api
from provider.twi_to_audio_api import audio_files_collection

router = APIRouter()

client = AsyncIOMotorClient(get_setting().MONGODB_URI)
database = client.get_default_database()
uploads_collection = database['uploads']
comments_collection = database['comments']

ALLOWED_EXTENSIONS = {".txt", ".pdf", ".docx", ".doc"}


def is_allowed_extension(filename: str) -> bool:
    return any(filename.endswith(ext) for ext in ALLOWED_EXTENSIONS)


@router.post('/upload/{c_type}', status_code=status.HTTP_201_CREATED)
async def upload_file(c_type: str, request: Request, upload_request: FileUploadModel, 
                      token_data: TokenData = Depends(get_current_user)):
    session_id = request.state.session_id
    base64_string = upload_request.file

    # Decode the base64 string to binary data
    try:
        logger.info(f'[{session_id}] about to decode to base64')
        file_data = base64.b64decode(base64_string)
    except Exception:
        logger.info(f'[{session_id}] error decoding base64 string')
        raise HTTPException(status_code=400, detail='Invalid base64 string')

    # Detect the file type
    kind = upload_request.file_extention
    if kind is None or kind not in ['txt', 'pdf', 'docx', 'doc']:
        logger.info(f'[{session_id}] error uploading file')
        raise HTTPException(status_code=400, detail='Invalid file type. Only .txt, .pdf, .docx, or .doc files are allowed.')

    if c_type.lower() != 'summarize' and c_type.lower() != 'full':
        raise HTTPException(status_code=400, detail='Bad request, path parameter requires type, summarize or full')
    logger.info(f'[{session_id}] building file metadata')
    file_id = str(uuid.uuid4())
    file_name = upload_request.file_name

    # Add converters here
    converters = {
        'docx': docx_to_text_converter.convert_docx_to_text,
        'doc': doc_to_text_conveter.convert_doc_to_text,
        'pdf': pdf_to_text_converter.convert_pdf_to_text,
        'txt': txt_to_text_conveter.convert_txt_to_text
    }
    conversion_function = converters.get(kind)
    text = await conversion_function(file_data, file_name, session_id)

    upload_dispatch = {
        'username': token_data.username,
        'file_name': file_name
    }

    if c_type.lower() == 'summarize':
        logger.info(f'[{session_id}] process is summarize, calling summarize api')
        audio_data = await summary_api.get_summary(text, upload_dispatch, session_id)
    else:
        logger.info(f'[{session_id}] process is full, calling ext to twi api')
        audio_data = await text_to_twi_api.convert_to_twi(text, upload_dispatch, session_id)

    logger.info(f'[{session_id}] extracting data from returned audio data')
    audio_file = audio_data['content']
    audio_id = audio_data['audio_id']


    logger.info(f'[{session_id}] creating meta data to return, encoding to base64 string')
    audio_string = base64.b64encode(audio_file).decode('utf-8')

    file_record = {
        '_id': file_id,
        'file_name': file_name,
        'content_type': kind,
        'username': token_data.username,
        'created_at': datetime.now(timezone.utc)
    }
    logger.info(f'[{session_id}] inserting record to database')
    await uploads_collection.insert_one(file_record)
    return JSONResponse(
    content={
        "status": "success", 
        "audio_id": audio_id,
        "audio_file": audio_string
    })

@router.get('/{audio_id}/download')
async def download_audio(audio_id: str, _: TokenData = Depends(get_current_user)):
    file_data = await audio_files_collection.find_one({'audio_id': audio_id})
    if not file_data:
        raise HTTPException(status_code=404, detail='Audio file not found')
    return StreamingResponse(io.BytesIO(file_data['file']), media_type='audio/mpeg',
                             headers={'Content-Disposition': f'attachment; filename={file_data["file_name"]}-audio.mp3'})


@router.post('/add-comment', status_code=201)
async def add_comment(comment: CommentModel, token_data: TokenData = Depends(get_current_user)):
    audio_file = await audio_files_collection.find_one({'audio_id': comment.audio_file_id})
    if audio_file['username'] != token_data.username:
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail='Unauthorized'
        )
    if audio_file is None:
        return HTTPException(
            status_code=404, detail='Audio file not found'
        )
    comment_data = {
        'comment_id': str(uuid.uuid4())[:5],
        'audio_id': comment.audio_id,
        'user': token_data.username,
        'comment': comment.comment,
        'rating': comment.rating,
        'created_at': datetime.now(timezone.utc),
    }
    try:
        await comments_collection.insert_one(comment_data)
        return {'message': 'Comment added'}
    except Exception:
        return HTTPException(
            status_code=500, detail='Error adding comment, try again later'
        )


@router.get('/history')
async def get_history(token_data: TokenData = Depends(get_current_user)):
    audio_files_cursor = audio_files_collection.find({'username': token_data.username}).sort('created_at', -1)
    history_file = await audio_files_cursor.to_list(length=None)
    history = []

    for data in history_file:
        file_data = data.get('file')
        if isinstance(file_data, bytes):
            file_data = base64.b64encode(file_data).decode('utf-8')
        elif not isinstance(file_data, str):
            file_data = None
        
        history_data = {
            'filename': data.get('file_name'),
            'audio_id': data.get('audio_id'),
            'created_at': data.get('created_at'),
            'size': data.get('size'),
            'audio_file': file_data
        }

        history.append(history_data)

    return history