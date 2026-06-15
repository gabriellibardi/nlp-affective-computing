from pathlib import Path

from pdf_reader import read_all_pdfs
from preprocessing import clean_text

OUTPUT_DIR = Path("../data/processed")
OUTPUT_DIR.mkdir(exist_ok=True)


def main():
    documents = read_all_pdfs(Path("../data/raw"))

    print(f"{len(documents)} artigos carregados")

    for name, text in documents.items():
        cleaned = clean_text(text)
        
        (OUTPUT_DIR / f"{name}.txt").write_text(
            cleaned,
            encoding="utf-8"
        )


if __name__ == "__main__":
    main()
