import re


def clean_text(text: str) -> str:
    # remove hífens de quebra de linha
    text = re.sub(r"-\s*\n\s*", "", text)

    # substitui quebras de linha por espaço
    text = re.sub(r"\n+", " ", text)

    # remove múltiplos espaços
    text = re.sub(r"\s+", " ", text)

    return text.strip()
