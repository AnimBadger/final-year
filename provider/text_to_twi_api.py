import httpx
import os
from fastapi import HTTPException
from dotenv import load_dotenv
from .twi_to_audio_api import convert_text_to_twi_audio
from config.logger_config import logger

load_dotenv()

NLP_KEY = os.getenv('NLP_KEY')

url = "https://translation-api.ghananlp.org/v1/translate"

headers = {
    'Content-Type': 'application/json',
    'Cache-Control': 'no-cache',
    'Ocp-Apim-Subscription-Key': NLP_KEY,
}


async def convert_to_twi(text: str, _: dict, session_id: str):
    logger.info(f'[{session_id}] started text to twi text generation')
    data = {
        'in': text,
        'lang': 'en-tw'
    }
    async with httpx.AsyncClient() as httpx_client:
        response = await httpx_client.post(url, headers=headers, json=data)
    if response.status_code == 200:
        logger.info(f'[{session_id}] successsfully generated twi text, calling text to audio')
        text = response.text
        return await convert_text_to_twi_audio(text, _, session_id)
    else:
        logger.info(f'[{session_id}] error generating twi text')
        raise HTTPException(status_code=400, detail='Could not process request, try again later')
