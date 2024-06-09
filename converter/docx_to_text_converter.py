import os

import docx2txt
from .regex_preprocessor import preprocess_text
from fastapi import UploadFile


async def convert_docx_to_text(docx_file: UploadFile):
    contents = await docx_file.read()
    tmp_file_path = f'/tmp/{docx_file.filename}'
    with open(tmp_file_path, 'wb') as temp_file:
        temp_file.write(contents)
    extracted_text = docx2txt.process(tmp_file_path)
    os.remove(tmp_file_path)
    return preprocess_text(extracted_text)

