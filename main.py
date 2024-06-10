import os

from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from config import get_setting
from fastapi.middleware.cors import CORSMiddleware
from middleware.session_middleware import SessionMiddleware
import uvicorn
from router import checker

from router.auth import authentication
from router.base import base_txt_to_twi

load_dotenv()
settings = get_setting()
app = FastAPI(debug=True)
app.add_middleware(SessionMiddleware)

origins = [
    'http://localhost',
    'http://localhost:8000',
    'http://13.51.241.186:80'
]

app.add_middleware(CORSMiddleware,
                   allow_origins=origins,
                   allow_credentials=True,
                   allow_methods='*',
                   allow_headers='*')

client = AsyncIOMotorClient(settings.MONGODB_URI)
database = client.get_default_database()

app.include_router(authentication.router, prefix='/api/v1/auth')
app.include_router(base_txt_to_twi.router, prefix='/api/v1/base/audio_files')
app.include_router(checker.router)


async def startup_db_client():
    app.mongodb_client = AsyncIOMotorClient(settings.MONGODB_URI)
    app.database = app.mongodb_client.get_default_database()


async def shutdown_db_client():
    await app.mongodb_client.close()


app.add_event_handler("startup", startup_db_client)
app.add_event_handler("shutdown", shutdown_db_client)

if __name__ == '__main__':
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 8000))
    uvicorn.run('main:app', host=HOST, port=PORT)
