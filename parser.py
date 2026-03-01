import PyPDF2
import docx
import io

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
            # python-docx needs a file-like object
            doc = docx.Document(file_storage)
            for paragraph in doc.paragraphs:
                extracted_text += paragraph.text + "\n"
        else:
            extracted_text = "Unsupported file format."
    except Exception as e:
        extracted_text = f"Error extracting text: {str(e)}"

    return extracted_text.strip()
