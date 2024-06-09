import httpx
from dotenv import load_dotenv
import os
from fastapi import HTTPException
from .text_to_twi_api import convert_to_twi

load_dotenv()

SUMMARY_API = os.getenv('SUMMARY_API')

url = "https://api.ai21.com/studio/v1/summarize"
headers = {
    'accept': 'application/json',
    'content-type': 'application/json',
    'Authorization': f'Bearer {SUMMARY_API}'
}


async def get_summary(text: str, _: dict):
    payload = {
        'sourceType': 'TEXT',
        'source': text
    }
    async with httpx.AsyncClient() as httpx_client:
        response = await httpx_client.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        response_data = response.json()
        summary = response_data['summary']
        return await convert_to_twi(summary, _)
    raise HTTPException(
        status_code=401, detail='Error processing request, retry after some time'
    )
