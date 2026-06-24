# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.3
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# ### Imports, function definitions and global variables

# %%
from pathlib import Path
from collections import Counter

from src.pdf_reader import extract_text_from_pdf
from src.preprocessing import (
    clean_text,
    remove_references,
    tokenize,
    remove_stopwords,
    lemmatize_tokens,
)
from src.extraction import extract_information_for_corpus


def dict_process(target: dict, process):
    return {key: process(value) for key, value in target.items()}


RAW_DIR = Path("./data/raw")
PROCESSED_DIR = Path("./data/processed")
NO_REFERENCES_DIR = Path("./data/no_references")

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
NO_REFERENCES_DIR.mkdir(parents=True, exist_ok=True)

pdf_files = list(RAW_DIR.glob("*.pdf"))

print(f"{len(pdf_files)} artigos encontrados")


def get_processed_text(pdf_path: Path, raw_text: str | None = None) -> str:
    """
    Obtém o texto limpo de um PDF.

    Se o texto já foi processado anteriormente, ele é carregado
    de data/processed. Caso contrário, o PDF é lido, limpo e salvo.
    """
    output_path = PROCESSED_DIR / f"{pdf_path.stem}.txt"

    if output_path.exists():
        return output_path.read_text(encoding="utf-8")

    if raw_text is None:
        raw_text = extract_text_from_pdf(pdf_path)

    processed_text = clean_text(raw_text)

    output_path.write_text(processed_text, encoding="utf-8")

    return processed_text


def process_text(pdf_path: Path, raw_text: str) -> str:
    return get_processed_text(pdf_path, raw_text=raw_text)


def get_text_without_references(
    pdf_path: Path,
    processed_text: str | None = None,
) -> str:
    """
    Obtém o texto sem referências bibliográficas.

    Se a versão sem referências já existe, ela é carregada.
    Caso contrário, as referências são removidas e o resultado é salvo.
    """
    output_path = NO_REFERENCES_DIR / f"{pdf_path.stem}.txt"

    if output_path.exists():
        return output_path.read_text(encoding="utf-8")

    if processed_text is None:
        processed_text = get_processed_text(pdf_path)

    text_without_references = remove_references(processed_text)

    output_path.write_text(text_without_references, encoding="utf-8")

    return text_without_references


def remove_text_references(pdf_path: Path, processed_text: str) -> str:
    return get_text_without_references(pdf_path, processed_text=processed_text)


# %% [markdown]
# ### Raw file reading and preprocessing

# %%
processed_text = {
    path: get_processed_text(path)
    for path in pdf_files
}

# %%
text_without_references = {
    path: get_text_without_references(path, processed_text[path])
    for path in pdf_files
}

# %%
for path, text in text_without_references.items():
    print("=" * 100)
    print(path.stem)
    print("=" * 100)
    print(text[:1000])
    print()

# %%
tokens = dict_process(text_without_references, tokenize)
tokens = dict_process(tokens, remove_stopwords)
lemmatized_tokens = dict_process(tokens, lemmatize_tokens)

# %%
all_lemmatized_tokens = [
    token
    for token_list in lemmatized_tokens.values()
    for token in token_list
]

print(Counter(all_lemmatized_tokens).most_common(10))


# %% [markdown]
# ### Etapa 2 - Extração de objetivo, problema, método e contribuição
#
# Nesta etapa, são extraídos trechos candidatos para:
#
# - objetivo do artigo;
# - problema ou lacuna de pesquisa;
# - método ou metodologia;
# - contribuição do artigo.
#
# A extração é feita sobre o texto sem referências, mas antes da tokenização,
# para preservar as sentenças originais.

# %%
step2_extractions = extract_information_for_corpus(text_without_references)


# %% [markdown]
# ### Visualização das extrações da Etapa 2

# %%
for article_name, extraction in step2_extractions.items():
    print("=" * 100)
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

    print()