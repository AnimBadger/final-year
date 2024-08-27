import httpx
from dotenv import load_dotenv
import os
from fastapi import HTTPException
from .text_to_twi_api import convert_to_twi
from config.logger_config import logger

load_dotenv()

SUMMARY_API = os.getenv('SUMMARY_API')

url = "https://api.ai21.com/studio/v1/summarize"
headers = {
    'accept': 'application/json',
    'content-type': 'application/json',
    'Authorization': f'Bearer {SUMMARY_API}'
}


async def get_summary(text: str, _: dict, session_id: str):
    logger.info(f'[{session_id}] started summary')
    payload = {
        'sourceType': 'TEXT',
        'source': text
    }
    async with httpx.AsyncClient() as httpx_client:
        response = await httpx_client.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        logger.info(f'[{session_id}] summary from api done, calling twi api')
        response_data = response.json()
        summary = response_data['summary']
        return await convert_to_twi(summary, _, session_id)
    logger.info(f'[{session_id}] error generating summary')
    raise HTTPException(
        status_code=400, detail='Error processing request, retry after some time'
    )
