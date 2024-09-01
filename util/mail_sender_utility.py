import httpx
import os
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential

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

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=5, max=60))
async def send_email(recipient: str, title: str, body: str):
    payload = {
        "ishtml": "true",
        "sendto": recipient,
        "name": sender,
        "replyTo": "noReply@gmail.com",
        "title": title,
        "body": body
    }
    async with httpx.AsyncClient() as httpx_client:
        response = await httpx_client.post(url, json=payload, headers=headers)

        if response.status_code == 200:
            return 'success'
        else:
            return 'failed'
