import io
from fastapi.responses import JSONResponse, StreamingResponse
import base64
from fastapi import APIRouter, HTTPException, Response, status, Depends, Request
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
    text = await conversion_function(file_data, file_name)

    upload_dispatch = {
        'username': token_data.username,
        'file_name': file_name
    }

    if c_type.lower() == 'summarize':
        audio_file = await summary_api.get_summary(text, upload_dispatch)
    else:
        audio_file = await text_to_twi_api.convert_to_twi(text, upload_dispatch)

    audio_string = base64.b64encode(audio_file).decode('utf-8')

    file_record = {
        '_id': file_id,
        'file_name': file_name,
        'content_type': kind,
        'username': token_data.username,
        'created_at': datetime.now(timezone.utc)
    }
    await uploads_collection.insert_one(file_record)
    return JSONResponse(
    content={
        "status": "success",
        "audio": audio_string
    })
'''
async def upload_file(c_type: str, request: Request, file: UploadFile = File(...),
                      token_data: TokenData = Depends(get_current_user)):
    session_id = request.state.session_id
    if not is_allowed_extension(file.filename):
        logger.info(f'[{session_id}] error uploading file')
        raise HTTPException(status_code=400,
                            detail='Invalid file extension. Only .txt, .pdf, .docx, or .doc files are allowed.')

    if c_type.lower() != 'summarize' and c_type.lower() != 'full':
        raise HTTPException(
            status_code=400, detail='Bad request, path parameter requires type, summarize or full'
        )
    file_id = str(uuid.uuid4())

    # add converters here
    file_extension = os.path.splitext(file.filename)[1].lower()
    file_name = os.path.splitext(file.filename)[0].lower()

    converters = {
        '.docx': docx_to_text_converter.convert_docx_to_text,
        '.doc': doc_to_text_conveter.convert_doc_to_text,
        '.pdf': pdf_to_text_converter.convert_pdf_to_text,
        '.txt': txt_to_text_conveter.convert_txt_to_text
    }
    conversion_function = converters.get(file_extension)
    text = await conversion_function(file)

    upload_dispatch = {
        'username': token_data.username,
        'file_name': file_name
    }

    if c_type.lower() == 'summarize':
        audio_id = await summary_api.get_summary(text, upload_dispatch)
    else:
        audio_id = await text_to_twi_api.convert_to_twi(text, upload_dispatch)

    file_data = {
        '_id': file_id,
        'file_name': file.filename,
        'content_type': file.content_type,
        'username': token_data.username,
        'created_at': datetime.utcnow()
    }
    await uploads_collection.insert_one(file_data)
    return UploadResponseModel(message='Success', file_id=audio_id)
'''

@router.get('/{audio_id}/download')
async def download_audio(audio_id: str, _: TokenData = Depends(get_current_user)):
    file_data = await audio_files_collection.find_one({'audio_id': audio_id})
    if not file_data:
        raise HTTPException(status_code=404, detail='Audio file not found')
    return StreamingResponse(io.BytesIO(file_data['file']), media_type='audio/mpeg',
                             headers={'Content-Disposition': f'attachment; filename={file_data["file_name"]}-audio.mp3'})


@router.get('/audio_files')
async def list_audio_files(token_data: TokenData = Depends(get_current_user)):
    files_cursor = audio_files_collection.find({'username': token_data.username})
    files = await files_cursor.to_list(length=None)

    listed_files = []
    for file in files:
        file_data = {
            'file_name': file['file_name'],
            'audio_id': file['audio_id'],
            'size': file['size']
        }
        listed_files.append(file_data)

    return listed_files


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
        'audio_id': comment .audio_file_id,
        'user': token_data.username,
        'comment': comment.comment,
        'created_at': datetime.utcnow()
    }
    try:
        await comments_collection.insert_one(comment_data)
        return {'message': 'Comment added'}
    except Exception:
        return HTTPException(
            status_code=500, detail='Error adding comment, try again later'
        )
