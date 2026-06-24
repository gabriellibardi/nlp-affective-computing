from pathlib import Path
from collections import Counter

from pdf_reader import extract_text_from_pdf
from preprocessing import (
    clean_text,
    remove_references,
    tokenize,
    remove_stopwords,
    lemmatize_tokens,
)
from extraction import extract_information_for_corpus


RAW_DIR = Path("./data/raw")
PROCESSED_DIR = Path("./data/processed")
NO_REFERENCES_DIR = Path("./data/no_references")


def get_processed_text(pdf_path: Path) -> str:
    """
    Obtém o texto limpo de um PDF.

    Se o texto já foi processado anteriormente, ele é carregado
    de data/processed. Caso contrário, o PDF é lido, limpo e salvo.
    """
    output_path = PROCESSED_DIR / f"{pdf_path.stem}.txt"

    if output_path.exists():
        return output_path.read_text(encoding="utf-8")

    raw_text = extract_text_from_pdf(pdf_path)
    processed_text = clean_text(raw_text)

    output_path.write_text(processed_text, encoding="utf-8")

    return processed_text


def get_text_without_references(name: str, processed_text: str) -> str:
    """
    Obtém o texto sem referências bibliográficas.

    Se a versão sem referências já existe, ela é carregada.
    Caso contrário, as referências são removidas e o resultado é salvo.
    """
    output_path = NO_REFERENCES_DIR / f"{name}.txt"

    if output_path.exists():
        return output_path.read_text(encoding="utf-8")

    text_without_references = remove_references(processed_text)

    output_path.write_text(text_without_references, encoding="utf-8")

    return text_without_references


def main() -> None:
    """
    Etapas:
    - Lê PDFs de data/raw.
    - Salva textos limpos em data/processed.
    - Salva textos sem referências em data/no_references.
    - Tokeniza, remove stopwords e aplica lemmatizing.
    - Executa a Etapa 2: extrai objetivo, problema, método e contribuição.
    - Salva as extrações em data/extractions/step2_extractions.json.
    """
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    NO_REFERENCES_DIR.mkdir(parents=True, exist_ok=True)

    pdf_files = list(RAW_DIR.glob("*.pdf"))

    print(f"{len(pdf_files)} artigos encontrados")

    texts_without_references = {}
    all_lemmatized_tokens = []

    for pdf_path in pdf_files:
        processed_text = get_processed_text(pdf_path)

        text_without_references = get_text_without_references(
            pdf_path.stem,
            processed_text,
        )

        texts_without_references[pdf_path] = text_without_references

        tokens = tokenize(text_without_references)
        tokens = remove_stopwords(tokens)
        lemmatized_tokens = lemmatize_tokens(tokens)

        all_lemmatized_tokens.extend(lemmatized_tokens)

        print(f"\n{pdf_path.stem}")
        print(f"Tokens após lemmatizing: {len(lemmatized_tokens)}")
        print(lemmatized_tokens[:50])

    print("\n" + "=" * 80)
    print("10 termos mais frequentes nos artigos")
    print("=" * 80)

    most_common_terms = Counter(all_lemmatized_tokens).most_common(10)

    for term, frequency in most_common_terms:
        print(f"{term}: {frequency}")

    print("\n" + "=" * 80)
    print("Etapa 2 - Extração de objetivo, problema, método e contribuição")
    print("=" * 80)

    step2_extractions = extract_information_for_corpus(texts_without_references)

    for article_name, extraction in step2_extractions.items():
        print("\n" + "=" * 100)
        print(f"ARTIGO: {article_name}")
        print("=" * 100)

        print("\nOBJETIVO:")
        if extraction["objective"]:
            for item in extraction["objective"]:
                print(f"- {item}")
        else:
            print("- Não encontrado automaticamente.")

        print("\nPROBLEMA:")
        if extraction["problem"]:
            for item in extraction["problem"]:
                print(f"- {item}")
        else:
            print("- Não encontrado automaticamente.")

        print("\nMÉTODO / METODOLOGIA:")
        if extraction["method"]:
            for item in extraction["method"]:
                print(f"- {item}")
        else:
            print("- Não encontrado automaticamente.")

        print("\nCONTRIBUIÇÃO:")
        if extraction["contribution"]:
            for item in extraction["contribution"]:
                print(f"- {item}")
        else:
            print("- Não encontrado automaticamente.")

        if extraction["review_notes"]:
            print("\nAVISOS PARA REVISÃO MANUAL:")
            for note in extraction["review_notes"]:
                print(f"- {note}")


if __name__ == "__main__":
    main()