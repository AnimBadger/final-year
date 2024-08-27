from .regex_preprocessor import preprocess_text
from config.logger_config import logger

async def convert_txt_to_text(file_data: bytes, _, session_id: str) -> str:
    logger.info(f'[{session_id}] decoding txt file to text')
    extracted_text = file_data.decode('utf-8')
    return preprocess_text(extracted_text, session_id)
