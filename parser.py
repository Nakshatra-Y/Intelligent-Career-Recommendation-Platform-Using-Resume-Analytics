import PyPDF2
import docx
import io
import re

def clean_text(text):
    """
    Cleans extracted text by removing symbols, special characters, 
    and extra whitespaces to optimize for keyword matching.
    """
    if not text:
        return ""
    # Remove special characters and symbols
    text = re.sub(r'[^\w\s\.]', ' ', text)
    # Remove extra spaces and newlines
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_text(file_storage):
    """
    Extracts text from a Flask FileStorage object.
    Supports .pdf and .docx file extensions.
    """
    filename = file_storage.filename.lower()
    extracted_text = ""

    try:
        if filename.endswith('.pdf'):
            reader = PyPDF2.PdfReader(file_storage)
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text = page.extract_text()
                if text:
                    extracted_text += text + "\n"
        elif filename.endswith('.docx'):
            doc = docx.Document(file_storage)
            for paragraph in doc.paragraphs:
                extracted_text += paragraph.text + "\n"
        else:
            extracted_text = "Unsupported file format."
    except Exception as e:
        extracted_text = f"Error extracting text: {str(e)}"

    # Apply cleaning before returning
    return clean_text(extracted_text)
