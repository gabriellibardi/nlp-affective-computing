from pathlib import Path

from pdf_reader import read_all_pdfs
from preprocessing import clean_text


def main():
    documents = read_all_pdfs(Path("../data/raw"))

    print(f"{len(documents)} artigos carregados")

    for name, text in documents.items():
        cleaned = clean_text(text)

        print("\n" + name)
        print(cleaned[:500])


if __name__ == "__main__":
    main()
