from .regex_preprocessor import preprocess_text

async def convert_txt_to_text(file_data: bytes, _) -> str:
    extracted_text = file_data.decode('utf-8')
    return preprocess_text(extracted_text)
