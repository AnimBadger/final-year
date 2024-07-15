import dotenv
import os

dotenv.load_dotenv()

MONGO_PASSWORD = os.getenv('MONGO_PASSWORD')
MONGO_USERNAME = os.getenv('MONGO_USERNAME')
MONGO_DB = os.getenv('MONGO_DB')


class Setting:
    MONGODB_URI = (f'mongodb+srv://{MONGO_USERNAME}:{MONGO_PASSWORD}@proj.pnwnb6u.mongodb.net/{MONGO_DB}?retryWrites'
                   f'=true&w'
                   f'=majority'
                   '&appName=proj')
    DEBUG = True
    LOG_LEVEL = 'DEBUG'
