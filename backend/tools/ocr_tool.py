import pytesseract
from PIL import Image
import fitz  # PyMuPDF
from pathlib import Path
import io


def ocr_image(image_path: str) -> str:
    try:
        img = Image.open(image_path)
        return pytesseract.image_to_string(img).strip()
    except Exception as e:
        return f"[OCR error: {e}]"


def ocr_pdf_pages(file_path: str) -> str:
    """Extract text from scanned PDFs using OCR on rendered pages."""
    text_parts = []
    try:
        doc = fitz.open(file_path)
        for page_num, page in enumerate(doc):
            pix = page.get_pixmap(dpi=200)
            img_bytes = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_bytes))
            page_text = pytesseract.image_to_string(img).strip()
            if page_text:
                text_parts.append(f"[Page {page_num + 1}]\n{page_text}")
        doc.close()
    except Exception as e:
        return f"[OCR PDF error: {e}]"
    return "\n\n".join(text_parts)


def extract_with_ocr(file_path: str) -> str:
    path = Path(file_path)
    ext = path.suffix.lower()
    if ext == ".pdf":
        return ocr_pdf_pages(file_path)
    elif ext in [".png", ".jpg", ".jpeg", ".tiff", ".bmp"]:
        return ocr_image(file_path)
    return "[OCR: unsupported file type]"
