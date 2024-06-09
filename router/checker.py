from fastapi import APIRouter
from config import get_setting
from motor.motor_asyncio import AsyncIOMotorClient

client = AsyncIOMotorClient(get_setting().MONGODB_URI)
database = client.get_default_database()
router = APIRouter()


@router.get('/health')
async def health_check():
    try:
        await database.command('ping')
        return {'message': 'All is alright'}
    except Exception as e:
        return {'message': 'Error', 'error_message': str(e)}
