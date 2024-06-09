from fastapi import UploadFile


async def convert_txt_to_text(txt_file: UploadFile) -> str:
    contents = await txt_file.read()
    extracted_text = contents.decode('utf-8')
    return extracted_text
