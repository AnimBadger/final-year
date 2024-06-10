from fastapi import APIRouter
from config import get_setting
from motor.motor_asyncio import AsyncIOMotorClient
from config.logger_config import logger

client = AsyncIOMotorClient(get_setting().MONGODB_URI)
database = client.get_default_database()
router = APIRouter()


@router.get('/health')
async def health_check():
    logger.info(f'Mongo client in environment {client}, database {database}')
    try:
        await database.command('ping')
        return {'message': 'All is alright'}
    except Exception as e:
        return {'message': 'Error', 'error_message': str(e)}
