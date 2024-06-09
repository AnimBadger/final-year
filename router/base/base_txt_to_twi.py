import io
from fastapi import APIRouter, HTTPException, status, UploadFile, File, Depends, Request
from motor.motor_asyncio import AsyncIOMotorClient
from config import get_setting
from fastapi.responses import StreamingResponse
from model.upload_file_model import UploadResponseModel
import uuid
import os
from config.logger_config import logger
from config.jwt_config import get_current_user
from model.jwt_model import TokenData
from datetime import datetime
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

ALLOWED_EXTENSIONS = {".txt", ".pdf", ".docx", ".doc"}


def is_allowed_extension(filename: str) -> bool:
    return any(filename.endswith(ext) for ext in ALLOWED_EXTENSIONS)


@router.post('/upload/{c_type}', response_model=UploadResponseModel, status_code=status.HTTP_201_CREATED)
async def upload_file(c_type: str, request: Request, file: UploadFile = File(...),
                      token_data: TokenData = Depends(get_current_user)):
    session_id = request.state.session_id
    if not is_allowed_extension(file.filename):
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
