import httpx
import os
from fastapi import HTTPException
from dotenv import load_dotenv
from .twi_to_audio_api import convert_text_to_twi

load_dotenv()

NLP_KEY = os.getenv('NLP_KEY')

url = "https://translation-api.ghananlp.org/v1/translate"

headers = {
    'Content-Type': 'application/json',
    'Cache-Control': 'no-cache',
    'Ocp-Apim-Subscription-Key': NLP_KEY,
}


async def convert_to_twi(text):
    data = {
        'in': text,
        'lang': 'en-tw'
    }
    async with httpx.AsyncClient() as httpx_client:
        response = await httpx_client.post(url, headers=headers, json=data)
    if response.status_code == 200:
        text = response.text
        return await convert_text_to_twi(text)
    else:
        raise HTTPException(status_code=401, detail='Could not process request, try again later')
