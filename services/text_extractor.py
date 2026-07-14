import fitz
import pytesseract

from pdf2image import convert_from_path

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


def extract_text(pdf_path):

    text = ""

    doc = fitz.open(pdf_path)

    for page in doc:
        text += page.get_text()

    doc.close()

    if text.strip():

        return text

    images = convert_from_path(
        pdf_path,
        poppler_path=r"C:\poppler\Library\bin"
    )

    ocr_text = ""

    for image in images:

        ocr_text += pytesseract.image_to_string(image)

    return ocr_text