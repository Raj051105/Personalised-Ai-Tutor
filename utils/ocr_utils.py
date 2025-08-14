# utils/ocr_utils.py
from pdf2image import convert_from_path
import pytesseract
from config import POPPLER_PATH, TESSERACT_PATH

pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

def ocr_page(pdf_path, page_no):
    """Run OCR on a specific page of a PDF."""
    img = convert_from_path(
        pdf_path,
        first_page=page_no,
        last_page=page_no,
        poppler_path=POPPLER_PATH,
        fmt="ppm"
    )[0]
    return pytesseract.image_to_string(img, lang="eng").strip()