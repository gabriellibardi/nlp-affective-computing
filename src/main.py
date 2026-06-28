"""
Ponto de entrada do pipeline de PLN para artigos científicos.

Fluxo geral, inspirado no projeto de referência:

1. leitura dos PDFs;
2. limpeza e separação de referências;
3. pré-processamento;
4. bag-of-words, bigramas e trigramas;
5. extração de objetivo, problema, metodologia, contribuição e trabalhos futuros;
6. exportação da ontologia JSON-LD;
7. geração automática dos gráficos a partir da ontologia.

Uso:
    python src/main.py
"""

from collections import Counter
from pathlib import Path
import nltk

from pdf_reader import extract_text_from_pdf
from preprocessing import clean_text, tokenize, remove_stopwords, lemmatize_tokens
from extraction import extract_information_for_corpus, split_references
from ontology import build_jsonld_corpus, ontology_summary, save_jsonld
from visualization import generate_all_visualizations

RAW_DIR = Path("./data/raw")
PROCESSED_DIR = Path("./data/processed")
NO_REFERENCES_DIR = Path("./data/no_references")
OUTPUT_DIR = Path("./data/ontology")
FIGURES_DIR = Path("./data/figures")
ONTOLOGY_OUTPUT = OUTPUT_DIR / "articles_ontology.jsonld"

def ensure_nltk_resources() -> None:
    """Garante os recursos básicos do NLTK usados no projeto."""
    resources = {
        "corpora/stopwords": "stopwords",
        "corpora/wordnet": "wordnet",
        "corpora/omw-1.4": "omw-1.4",
    }

    for resource_path, package in resources.items():
        try:
            nltk.data.find(resource_path)
        except LookupError:
            nltk.download(package, quiet=True)


def ngrams(tokens: list[str], n: int) -> Counter:
    """Gera n-gramas simples a partir de uma lista de tokens"""
    if len(tokens) < n:
        return Counter()

    grams = []
    for i in range(len(tokens) - n + 1):
        gram = tokens[i:i + n]
        if len(set(gram)) > 1:
            grams.append(" ".join(gram))

    return Counter(grams)


def get_processed_text(pdf_path: Path) -> str:
    """Lê o PDF, limpa o texto e usa cache em data/processed"""
    output_path = PROCESSED_DIR / f"{pdf_path.stem}.txt"

    if output_path.exists():
        return output_path.read_text(encoding="utf-8")

    raw_text = extract_text_from_pdf(pdf_path)
    processed_text = clean_text(raw_text)
    output_path.write_text(processed_text, encoding="utf-8")
    return processed_text


def get_body_and_references(name: str, processed_text: str) -> tuple[str, list[str]]:
    """Separa texto sem referências e referências"""
    body_path = NO_REFERENCES_DIR / f"{name}.txt"
    body, references = split_references(processed_text)

    if body_path.exists():
        body = body_path.read_text(encoding="utf-8")
    else:
        body_path.write_text(body, encoding="utf-8")

    return body, references


def preprocess_body_text(body_text: str) -> list[str]:
    """Executa tokenização, remoção de stopwords e lematização"""
    tokens = tokenize(body_text)
    tokens = remove_stopwords(tokens)
    return lemmatize_tokens(tokens)


def format_top_terms(title: str, terms: list[tuple[str, int]]) -> str:
    """Formata uma lista de termos frequentes em texto"""
    lines = [title, "=" * len(title)]

    if not terms:
        lines.append("(sem dados)")
        return "\n".join(lines)

    max_freq = max(freq for _, freq in terms) or 1
    for rank, (term, freq) in enumerate(terms, 1):
        bar = "-" * min(int(freq / max_freq * 30), 30)
        lines.append(f"{rank:2d}. {term:<35s} {freq:5d}  {bar}")

    return "\n".join(lines)


def print_stage(title: str) -> None:
    print("\n" + "-" * 50)
    print(title)
    print("-" * 50)


def main() -> None:
    ensure_nltk_resources()

    for directory in [RAW_DIR, PROCESSED_DIR, NO_REFERENCES_DIR, OUTPUT_DIR, FIGURES_DIR]:
        directory.mkdir(parents=True, exist_ok=True)

    print_stage("1 - Lendo PDFs")
    pdf_files = sorted(RAW_DIR.glob("*.pdf"))
    print(f"Artigos encontrados em {RAW_DIR}: {len(pdf_files)}")

    texts_without_references: dict[Path, str] = {}
    references_by_article: dict[Path, list[str]] = {}
    tokens_by_article: dict[str, list[str]] = {}
    simplified_categorized: dict[str, dict] = {}

    all_tokens: list[str] = []
    bow_global = Counter()

    for pdf_path in pdf_files:
        processed_text = get_processed_text(pdf_path)
        body_text, references = get_body_and_references(pdf_path.stem, processed_text)
        tokens = preprocess_body_text(body_text)

        texts_without_references[pdf_path] = body_text
        references_by_article[pdf_path] = references
        tokens_by_article[pdf_path.stem] = tokens

        all_tokens.extend(tokens)
        bow_global.update(tokens)

        simplified_categorized[pdf_path.stem] = {
            "filename": pdf_path.name,
            "tokens": len(tokens),
            "references": len(references),
        }

        print(f"- {pdf_path.name}: {len(tokens)} tokens | {len(references)} referências")

    print_stage("2 - Modelos de linguagem: BoW")

    top_uniterms = bow_global.most_common(10)

    for term, freq in top_uniterms:
        print(f"- {term:<35s} {freq:5d}")

    print_stage("3 - Extraindo objetivo, problema, metodologia, contribuição e trabalhos futuros")

    step2_extractions = extract_information_for_corpus(texts_without_references, references_by_article=references_by_article)

    for article_id, info in step2_extractions.items():
        # Completa a saída categorizada simplificada com título e ano extraídos.
        simplified_categorized.setdefault(article_id, {})
        simplified_categorized[article_id].update({
            "stage2_fields_found": sum(
                1
                for field in ["objective", "problem", "method", "contribution", "future_work"]
                if info.get(field)
            ),
        })

        print(article_id, f" - Campos extraídos: {simplified_categorized[article_id]['stage2_fields_found']}/5\n")

    print_stage("4 - Construindo ontologia JSON-LD")

    ontology = build_jsonld_corpus(extractions=step2_extractions, most_common_terms=top_uniterms, tokens_by_article=tokens_by_article)
    save_jsonld(ontology, ONTOLOGY_OUTPUT)

    print(ontology_summary(ontology))
    print(f"\nOntologia salva em: {ONTOLOGY_OUTPUT}")

    print_stage("5 - Gerando visualizações a partir da ontologia")

    generated_figures = generate_all_visualizations(ontology_path=ONTOLOGY_OUTPUT, output_dir=FIGURES_DIR)

    print("\nArquivos finais gerados:")
    print(f"- {ONTOLOGY_OUTPUT}")

    print("\nGráficos gerados:")
    for path in generated_figures:
        print(f"- {path}")

if __name__ == "__main__":
    main()