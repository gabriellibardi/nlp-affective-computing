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

def dict_process(target: dict, process):
    return {key: process(value) for key, value in target.items()}

RAW_DIR = Path("./data/raw")
PROCESSED_DIR = Path("./data/processed")
NO_REFERENCES_DIR = Path("./data/no_references")

pdf_files = list(RAW_DIR.glob("*.pdf"))
print(f"{len(pdf_files)} artigos encontrados")

def get_processed_text(pdf_path: Path, raw_text: str=None) -> str:
    """
    Obtém o texto limpo de um PDF.

    Se o texto já foi processado anteriormente, ele é carregado
    de data/processed. Caso contrário, o PDF é lido, limpo e salvo.
    """
    output_path = PROCESSED_DIR / f"{pdf_path.stem}.txt"

    if output_path.exists():
        return output_path.read_text(encoding="utf-8")

    if raw_text == None:
        raw_text = extract_text_from_pdf(pdf_path)
    processed_text = clean_text(raw_text)

    output_path.write_text(processed_text, encoding="utf-8")

    return processed_text

def process_text(pdf_path: Path, raw_text:str) -> str:
    return get_processed_text(pdf_path, raw_text=raw_text)

def get_text_without_references(pdf_path: Path, processed_text: str=None) -> str:
    """
    Obtém o texto sem referências bibliográficas.

    Se a versão sem referências já existe, ela é carregada.
    Caso contrário, as referências são removidas e o resultado é salvo.
    """
    output_path = NO_REFERENCES_DIR / f"{pdf_path.stem}.txt"

    if output_path.exists():
        return output_path.read_text(encoding="utf-8")

    if processed_text == None:
        get_processed_text(pdf_path)
    text_without_references = remove_references(processed_text)

    output_path.write_text(text_without_references, encoding="utf-8")

    return text_without_references

def remove_text_references(pdf_path: Path, processed_text):
    return get_text_without_references(pdf_path, processed_text=processed_text)


# %% [markdown]
# ### Raw file reading and preprocessing

# %%
processed_text = {path: get_processed_text(path) for path in pdf_files}

# %%
text_without_references = {path: get_text_without_references(path) for path in pdf_files}

# %%
print(text_without_references)

# %%
tokens = dict_process(text_without_references, tokenize)
tokens = dict_process(tokens, remove_stopwords)
lemmatized_tokens = dict_process(tokens, lemmatize_tokens)

# %%
all_lemmatized_tokens = [t for token_list in lemmatized_tokens.values() for t in token_list]
print(Counter(all_lemmatized_tokens).most_common(10))
