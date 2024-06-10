import os
from dotenv import load_dotenv
from config.logger_config import logger

load_dotenv()


def get_setting():
    env = os.getenv("ENV", "development")
    logger.info(f'Environment found {env}')

    if env == 'development':
        from .development import Setting

    elif env == 'staging':
        from .staging import Setting

    else:
        raise ValueError(f'Unknown environment {env}')
    logger.log(f'Settings? {Setting}')
    return Setting
