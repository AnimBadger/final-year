import httpx
import os
from dotenv import load_dotenv
from fastapi import HTTPException

load_dotenv()
RAPID_API_KEY = os.getenv('RAPID_API_KEY')

url = "https://rapidmail.p.rapidapi.com/"
sender = 'Text2Twi'
reply_to = 'noReply'

headers = {
    "x-rapidapi-key": RAPID_API_KEY,
    "x-rapidapi-host": "rapidmail.p.rapidapi.com",
    "Content-Type": "application/json"
}


async def send_email(recipient: str, title: str, body: str):
    if recipient is None:
        return 'failed'

    payload = {
        "ishtml": "true",
        "sendto": recipient,
        "name": sender,
        "replyTo": "anim.ansah.stephen@gmail.com",
        "title": title,
        "body": body
    }
    async with httpx.AsyncClient() as httpx_client:
        response = await httpx_client.post(url, json=payload, headers=headers)

        if response.status_code == 200:
            return 'success'
        else:
            return 'failed'
