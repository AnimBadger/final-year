import asyncio
import os
from dotenv import load_dotenv
from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from config import get_setting
import uuid
from datetime import datetime, timezone
import httpx
from bson import Binary
from config.logger_config import logger

load_dotenv()

client = AsyncIOMotorClient(get_setting().MONGODB_URI)
database = client.get_default_database()
audio_files_collection = database['audio_files']

NLP_KEY = os.getenv('NLP_KEY')
url = "https://translation-api.ghananlp.org/tts/v1/tts"

headers = {
    'Content-Type': 'application/json',
    'Cache-Control': 'no-cache',
    'Ocp-Apim-Subscription-Key': NLP_KEY,
}


async def convert_text_to_twi_audio(text: str, dispatch: dict, session_id: str):
    logger.info(f'[{session_id}] started processing to twi audio')
    data = {
        "text": text,
        "language": 'tw'
    }

    timeout = httpx.Timeout(30.0, connect=10.0)
    retries = 3

    for attempt in range(retries):
        try:
            async with httpx.AsyncClient(timeout=timeout) as httpx_client:
                response = await httpx_client.post(url, headers=headers, json=data)
                response.raise_for_status()
                content = response.content
                logger.info(f'[{session_id}] done generating audio, about to build metadata, success')
                break
        except (httpx.HTTPStatusError, httpx.RequestError) as exc:
            if attempt == retries - 1:
                logger.info(f'[{session_id}] Could not convert to twi audio, time out')
                raise HTTPException(
                    status_code=400, detail=f'Failed after {retries} attempts: {str(exc)}'
                )

            await asyncio.sleep(2 ** attempt)

    if content is None:
        logger.info(f'[{session_id}] Error generating audio')
        raise HTTPException(
            status_code=500, detail='Error obtaining audio file'
        )
    logger.info(f'[{session_id}] building metadata to save and return after successful conversion')
    audio_id = str(uuid.uuid4())
    size = await calculate_to_mb(len(content))
    file_data = {
        'username': dispatch['username'],
        'file_name': dispatch['file_name'] + 'audio',
        'audio_id': audio_id,
        'file': Binary(content),
        'created_at': datetime.now(timezone.utc),
        'size': str(round(size, 2)) + 'mb'
    }

    await audio_files_collection.insert_one(file_data)
    return {"content": content, "audio_id": audio_id}


async def calculate_to_mb(size_in_byte: int) -> float:
    return size_in_byte / (1024 * 1024)
