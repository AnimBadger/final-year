import httpx
import os
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential

load_dotenv()
SENDINBLUE_API_KEY = os.getenv('SENDINBLUE_API_KEY')

url = "https://api.sendinblue.com/v3/smtp/email"
sender_name = 'Text2Twi'
sender_email = 'anim.ansah.stephen@gmail.com'

headers = {
    "api-key": SENDINBLUE_API_KEY,
    "Content-Type": "application/json"
}

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=5, max=60))
async def send_email(recipient: str, title: str, body: str):
    payload = {
        "sender": {"name": sender_name, "email": sender_email},
        "to": [{"email": recipient}],
        "subject": title,
        "htmlContent": body,
        "replyTo": {"email": sender_email}
    }
    
    async with httpx.AsyncClient() as httpx_client:
        response = await httpx_client.post(url, json=payload, headers=headers)

        if response.status_code == 201:
            return 'success'
        else:
            return f'failed: {response.status_code} - {response.text}'
