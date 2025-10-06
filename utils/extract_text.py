import os
from pdfminer.high_level import extract_text as pdf_extract_text
from docx import Document


def extract_text_from_file(file_path: str) -> str:
	_, ext = os.path.splitext(file_path.lower())
	if ext == ".pdf":
		return _extract_text_from_pdf(file_path)
	if ext == ".docx":
		return _extract_text_from_docx(file_path)
	if ext == ".txt":
		return _extract_text_from_txt(file_path)
	raise ValueError("Unsupported file type. Please provide PDF, DOCX, or TXT.")


def _extract_text_from_pdf(file_path: str) -> str:
	text = pdf_extract_text(file_path)
	return text.strip()


def _extract_text_from_docx(file_path: str) -> str:
	document = Document(file_path)
	paragraphs = [p.text for p in document.paragraphs]
	text = "\n".join(p for p in paragraphs if p)
	return text.strip()


def _extract_text_from_txt(file_path: str) -> str:
	with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
		return f.read().strip()
