import fitz  # PyMuPDF
import pdfplumber
from docx import Document as DocxDocument
from pathlib import Path
from typing import List, Dict
import re


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk:
            chunks.append(chunk)
    return chunks


def extract_text_pymupdf(file_path: str) -> str:
    text = ""
    try:
        doc = fitz.open(file_path)
        for page in doc:
            text += page.get_text()
        doc.close()
    except Exception as e:
        text = f"[PyMuPDF error: {e}]"
    return text.strip()


def extract_text_pdfplumber(file_path: str) -> str:
    text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        text = f"[pdfplumber error: {e}]"
    return text.strip()


def extract_text_docx(file_path: str) -> str:
    try:
        doc = DocxDocument(file_path)
        return "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
    except Exception as e:
        return f"[DOCX error: {e}]"


def extract_text_from_file(file_path: str) -> Dict:
    path = Path(file_path)
    ext = path.suffix.lower()
    text = ""
    method = "unknown"

    if ext == ".pdf":
        text = extract_text_pymupdf(file_path)
        method = "pymupdf"
        if len(text) < 50:
            text = extract_text_pdfplumber(file_path)
            method = "pdfplumber"
    elif ext in [".docx", ".doc"]:
        text = extract_text_docx(file_path)
        method = "python-docx"
    elif ext == ".txt":
        text = path.read_text(encoding="utf-8", errors="ignore")
        method = "plaintext"
    else:
        text = f"Unsupported file type: {ext}"

    # Clean text
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)

    chunks = chunk_text(text)
    return {
        "file_path": file_path,
        "filename": path.name,
        "file_type": ext,
        "extraction_method": method,
        "text": text,
        "chunks": chunks,
        "char_count": len(text),
        "chunk_count": len(chunks),
    }
