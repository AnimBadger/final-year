import os
from fastapi import UploadFile
import textract
from .regex_preprocessor import preprocess_text


async def convert_doc_to_text(doc_file: UploadFile):
    contents = await doc_file.read()
    tmp_file_path = f'/tmp/{doc_file.filename}'
    with open(tmp_file_path, 'wb') as temp_file:
        temp_file.write(contents)
    extracted_text = textract.process(temp_file)
    os.remove(tmp_file_path)
    return preprocess_text(extracted_text)
