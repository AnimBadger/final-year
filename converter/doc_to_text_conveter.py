import os
from config.logger_config import logger
import textract
from .regex_preprocessor import preprocess_text


async def convert_doc_to_text(file_data: bytes, file_name: str, session_id: str) -> str:
    logger.info(f'[{session_id}] extracting text from doc')
    tmp_file_path = os.join('/tmp', file_name)
    
    with open(tmp_file_path, 'wb') as temp_file:
        temp_file.write(file_data)
    
    extracted_text = textract.process(tmp_file_path)
    os.remove(tmp_file_path)
    return preprocess_text(extracted_text.decode('utf-8'), session_id)