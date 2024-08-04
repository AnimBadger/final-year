import os
from fastapi import UploadFile
import textract
from .regex_preprocessor import preprocess_text


async def convert_doc_to_text(file_data: bytes, file_name: str) -> str:
    tmp_file_path = f'/tmp/{file_name}'
    
    with open(tmp_file_path, 'wb') as temp_file:
        temp_file.write(file_data)
    
    extracted_text = textract.process(tmp_file_path)
    os.remove(tmp_file_path)
    return preprocess_text(extracted_text.decode('utf-8'))