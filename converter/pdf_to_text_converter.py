import PyPDF2
from .regex_preprocessor import preprocess_text
import os
from config.logger_config import logger


async def convert_pdf_to_text(file_data: bytes, file_name: str, session_id: str) -> str:
    logger.info(f'[{session_id}] extracting text from pdf')
    tmp_file_path = os.path.join('/tmp', file_name)

    with open(tmp_file_path, 'wb') as tmp_file:
        tmp_file.write(file_data)

    with open(tmp_file_path, 'rb') as tmp_file:
        reader = PyPDF2.PdfReader(tmp_file)
        extracted_text = ''

        for page_number in range(len(reader.pages)):
            page = reader.pages[page_number]
            page_text = page.extract_text()
            page_text = preprocess_text(page_text, session_id)
            extracted_text += page_text

    os.remove(tmp_file_path)
    return extracted_text