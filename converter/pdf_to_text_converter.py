import PyPDF2
from .regex_preprocessor import preprocess_text
import os


async def convert_pdf_to_text(file_data: bytes, file_name: str) -> str:
    tmp_file_path = f'/tmp/{file_name}'

    with open(tmp_file_path, 'wb') as tmp_file:
        tmp_file.write(file_data)

    with open(tmp_file_path, 'rb') as tmp_file:
        reader = PyPDF2.PdfReader(tmp_file)
        extracted_text = ''

        for page_number in range(len(reader.pages)):
            page = reader.pages[page_number]
            page_text = page.extract_text()
            page_text = preprocess_text(page_text)
            extracted_text += page_text

    os.remove(tmp_file_path)
    return extracted_text