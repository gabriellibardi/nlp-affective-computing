import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

lemmatizer = WordNetLemmatizer()


def get_stopwords() -> set[str]:
    """
    Carrega as stopwords da língua inglesa.
    """
    return set(stopwords.words("english"))


def clean_text(text: str) -> str:
    """
    Realiza a limpeza inicial do texto extraído do PDF.
    """
    text = re.sub(r"-\s*\n\s*", "", text)
    text = re.sub(r"\n+", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def remove_references(text: str) -> str:
    """
    Remove a seção de referências bibliográficas do artigo.
    """
    lower_text = text.lower()

    patterns = [
        r"\breferences\b",
        r"\bbibliography\b",
    ]

    positions = []

    for pattern in patterns:
        match = re.search(pattern, lower_text)

        if match:
            positions.append(match.start())

    if not positions:
        return text

    return text[:min(positions)].strip()


def tokenize(text: str) -> list[str]:
    """
    Divide o texto em tokens compostos apenas por letras.
    """
    text = text.lower()
    text = re.sub(r"[^a-z\s]", " ", text)

    return text.split()


def remove_stopwords(tokens: list[str]) -> list[str]:
    """
    Remove stopwords da língua inglesa.
    """
    stop_words = get_stopwords()

    return [
        token
        for token in tokens
        if token not in stop_words and len(token) > 2
    ]


def lemmatize_tokens(tokens: list[str]) -> list[str]:
    """
    Aplica lematização nos tokens usando WordNetLemmatizer.
    """
    return [lemmatizer.lemmatize(token) for token in tokens]
