import os
from config.logger_config import logger
import docx2txt
from .regex_preprocessor import preprocess_text


async def convert_docx_to_text(file_data: bytes, file_name: str, session_id: str) -> str:
    logger.info(f'[{session_id}] about to extract file data from docx to text')
    tmp_file_path = f'/tmp/{file_name}'
    
    with open(tmp_file_path, 'wb') as temp_file:
        temp_file.write(file_data)
    
    extracted_text = docx2txt.process(tmp_file_path)
    os.remove(tmp_file_path)
    return preprocess_text(extracted_text, session_id)
