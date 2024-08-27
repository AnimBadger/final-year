import re
from config.logger_config import logger

def preprocess_text(text, session_id):
    logger.info(f'[{session_id}] processing file to remove symbols')
    # Add spaces between concatenated words
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)

    # Remove unwanted characters
    text = re.sub(r'[•●]', '', text)

    # Replace multiple spaces with a single space
    text = re.sub(r'\s+', ' ', text)

    # Remove leading and trailing spaces
    text = text.strip()

    # Handle line breaks and hyphenation
    text = re.sub(r'(\w)-\s+(\w)', r'\1\2', text)

    # Remove special characters and symbols
    text = re.sub(r'[^\w\s.,!?:;\'"()\[\]{}\-—]', '', text)

    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)

    return text
