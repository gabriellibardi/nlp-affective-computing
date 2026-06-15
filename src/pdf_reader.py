from pathlib import Path
from pypdf import PdfReader


def extract_text(pdf_path: Path) -> str:
    reader = PdfReader(pdf_path)

    text = ""

    for page in reader.pages:
        page_text = page.extract_text()

        if page_text:
            text += page_text + "\n"

    return text


def read_all_pdfs(directory: Path) -> dict[str, str]:
    documents = {}

    for pdf_file in directory.glob("*.pdf"):
        documents[pdf_file.stem] = extract_text(pdf_file)

    return documents
