"""
Extração simples de informações de artigos científicos.

Comportamento inspirado no arquivo de referência:
1. separa referências;
2. divide o artigo em regiões aproximadas;
3. divide em frases;
4. busca trechos por padrões;
5. retorna listas de trechos literais.
"""

import re
from pathlib import Path
from typing import Mapping

# Texto e frases

SPACE_RE = re.compile(r"\s+")

ABBREVIATIONS = [
    "e.g.", "i.e.", "et al.", "etc.", "vs.",
    "Fig.", "Eq.", "Sec.", "Dr.", "Prof.", "No.",
]

def normalize_text(text: str) -> str:
    """Normaliza espaços duplicados"""
    return SPACE_RE.sub(" ", text or "").strip()

def split_text(text: str) -> list[str]:
    """Divide texto em frases protegendo abreviações comuns"""
    text = normalize_text(text)

    if not text:
        return []

    protected = text
    placeholders = {}

    for i, abbr in enumerate(ABBREVIATIONS):
        token = f"@@ABBR{i}@@"
        placeholders[token] = abbr
        protected = re.sub(re.escape(abbr), token, protected, flags=re.IGNORECASE)

    raw_sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9(\"'])", protected)

    sentences = []

    for sentence in raw_sentences:
        for token, abbr in placeholders.items():
            sentence = sentence.replace(token, abbr)

        sentence = normalize_text(sentence)

        if 35 <= len(sentence) <= 1100 and not is_noise_sentence(sentence):
            sentences.append(sentence)

    return sentences

def is_noise_sentence(sentence: str) -> bool:
    """Remove frases claramente vindas de cabeçalho, rodapé ou copyright"""
    lower = sentence.lower()

    noise = [
        "permission to make",
        "copyright",
        "all rights reserved",
        "publication date",
        "pacm on human-computer interaction",
        "acm reference format",
        "doi.org",
    ]

    return any(item in lower for item in noise)

def make_excerpt(sentences: list[str], index: int) -> str:
    """Retorna a frase encontrada junto com a próxima, quando couber"""
    excerpt = sentences[index]

    if index + 1 < len(sentences):
        next_sentence = sentences[index + 1]

        if len(excerpt) + len(next_sentence) <= 900:
            excerpt = f"{excerpt} {next_sentence}"

    return excerpt

# Referências

REFERENCE_HEADING_RE = re.compile(r"\b(?:references|bibliography|acm references|literature cited)\b", re.IGNORECASE)

def clean_reference(reference: str) -> str:
    """Limpa marcador inicial e pequenos ruídos de referência"""
    reference = normalize_text(reference)
    reference = re.sub(r"^\s*(?:\[\d+\]|\(\d+\)|\d+\.)\s*", "", reference)

    reference = re.sub(
        r"PACM on Human-Computer Interaction.*?Publication date:\s*[A-Za-z]+\s+\d{4}\.?",
        " ",
        reference,
        flags=re.IGNORECASE,
    )

    return normalize_text(reference)

def split_references(text: str) -> tuple[str, list[str]]:
    """Separa corpo do artigo e referências"""
    text = normalize_text(text)
    matches = list(REFERENCE_HEADING_RE.finditer(text))

    if not matches:
        return text, []

    # Evita pegar "references" citado cedo demais
    half = len(text) * 0.5
    match = next((m for m in matches if m.start() > half), matches[-1])

    body = text[: match.start()].strip()
    refs_text = text[match.end():].strip()

    if not refs_text:
        return body, []

    parts = re.split(r"(?=(?:\[\d{1,3}\]|\b\d{1,3}\.\s+[A-Z]))", refs_text)

    references = [
        clean_reference(part)
        for part in parts
        if len(clean_reference(part)) > 35
    ]

    return body, references if references else [clean_reference(refs_text)]

# seções

HEADINGS = [
    "abstract",
    "keywords",
    "introduction",
    "related work",
    "background",
    "literature review",
    "method",
    "methods",
    "methodology",
    "materials and methods",
    "approach",
    "proposed approach",
    "experiment",
    "experiments",
    "experimental setup",
    "results",
    "evaluation",
    "discussion",
    "conclusion",
    "conclusions",
    "final remarks",
    "references",
]

def heading_regex(headings: list[str]) -> re.Pattern:
    escaped = [re.escape(h) for h in sorted(headings, key=len, reverse=True)]

    return re.compile(
        r"(?:^|\s)"
        r"(?:\d+(?:\.\d+)*\.?\s*)?"
        r"(?:" + "|".join(escaped) + r")"
        r"(?:\s|:|\.)",
        re.IGNORECASE,
    )


def extract_section(text: str, start_headings: list[str], fallback: str) -> str:
    """Extrai uma seção aproximada"""
    text = normalize_text(text)

    start_re = heading_regex(start_headings)
    all_re = heading_regex(HEADINGS)

    start_match = start_re.search(text)

    if start_match:
        start = start_match.end()
        next_match = all_re.search(text, pos=start + 60)
        end = next_match.start() if next_match else len(text)

        section = text[start:end].strip()

        if len(section) > 80:
            return section

    if fallback == "start":
        return text[: int(len(text) * 0.35)]

    if fallback == "middle":
        return text[int(len(text) * 0.20): int(len(text) * 0.80)]

    if fallback == "end":
        return text[int(len(text) * 0.65):]

    return text

# padrões

OBJECTIVE_PATTERNS = [
    r"\bthe objective of this (paper|article|study|work|research) is\b",
    r"\bthe aim of this (paper|article|study|work|research) is\b",
    r"\bthe goal of this (paper|article|study|work|research) is\b",
    r"\bthe purpose of this (paper|article|study|work|research) is\b",
    r"\bthis (paper|article|study|work|research) aims to\b",
    r"\bwe aim to\b",
    r"\bin this (paper|article|study|work), we\b",
    r"\bthis (paper|article|study|work|research) investigates\b",
    r"\bthis (paper|article|study|work|research) explores\b",
    r"\bthis (paper|article|study|work|research) examines\b",
]

PROBLEM_PATTERNS = [
    r"\bproblem\b",
    r"\bchallenge\b",
    r"\bissue\b",
    r"\bgap\b",
    r"\blimitation\b",
    r"\black of\b",
    r"\bthere is a need\b",
    r"\bthere remains\b",
    r"\blittle is known\b",
    r"\bremains unclear\b",
    r"\bis difficult\b",
    r"\bfail to\b",
    r"\bfails to\b",
    r"\bdespite\b",
]

METHOD_PATTERNS = [
    r"\bmethod\b",
    r"\bmethodology\b",
    r"\bapproach\b",
    r"\bframework\b",
    r"\btechnique\b",
    r"\balgorithm\b",
    r"\bdataset\b",
    r"\bcorpus\b",
    r"\bexperiment\b",
    r"\bevaluation\b",
    r"\bparticipants?\b",
    r"\binterviews?\b",
    r"\bsurvey\b",
    r"\bwe used\b",
    r"\bwe conducted\b",
    r"\bwe collected\b",
    r"\bwe developed\b",
    r"\bwe evaluated\b",
]

CONTRIBUTION_PATTERNS = [
    r"\bcontribution\b",
    r"\bcontributions\b",
    r"\bcontribute\b",
    r"\bwe contribute\b",
    r"\bwe propose\b",
    r"\bwe present\b",
    r"\bwe introduce\b",
    r"\bwe provide\b",
    r"\bwe demonstrate\b",
    r"\bthis (paper|article|study|work) proposes\b",
    r"\bthis (paper|article|study|work) presents\b",
    r"\bthis (paper|article|study|work) introduces\b",
]

FUTURE_WORK_PATTERNS = [
    r"\bfuture work\b",
    r"\bfuture research\b",
    r"\bfuture studies\b",
    r"\bfuture direction\b",
    r"\bfuture directions\b",
    r"\bfurther work\b",
    r"\bfurther research\b",
    r"\bin the future\b",
    r"\bwe plan to\b",
    r"\bwe intend to\b",
]

# Extração

def find_excerpts(text: str, patterns: list[str], limit: int = 2, exclude: list[str] | None = None) -> list[str]:
    """Busca frases que casam com os padrões"""
    sentences = split_text(text)
    results = []
    seen = set()

    excluded = {
        normalize_text(item).lower()[:180]
        for item in (exclude or [])
    }

    for i, sentence in enumerate(sentences):
        if any(re.search(pattern, sentence, flags=re.IGNORECASE) for pattern in patterns):
            excerpt = make_excerpt(sentences, i)
            key = normalize_text(excerpt).lower()[:180]

            if key not in seen and key not in excluded:
                results.append(excerpt)
                seen.add(key)

        if len(results) >= limit:
            break

    return results

def extract_info(paper: dict) -> dict:
    """Extrai informações de um artigo já separado em regiões"""
    intro = paper.get("intro_text", "") or paper.get("abstract", "")
    method_text = paper.get("method_text", "") or paper.get("body_text", "")
    conclusion = paper.get("conclusion_text", "")
    body = paper.get("body_text", "")

    objective = find_excerpts(intro, OBJECTIVE_PATTERNS, limit=2)

    if not objective:
        objective = find_excerpts(body, OBJECTIVE_PATTERNS, limit=1)

    problem = find_excerpts(intro, PROBLEM_PATTERNS, limit=2)

    if not problem:
        problem = find_excerpts(body, PROBLEM_PATTERNS, limit=1)

    method = find_excerpts(method_text, METHOD_PATTERNS, limit=2)

    if not method:
        method = find_excerpts(body, METHOD_PATTERNS, limit=1)

    contribution = find_excerpts(
        f"{intro} {conclusion}",
        CONTRIBUTION_PATTERNS,
        limit=3,
        exclude=objective,
    )

    if not contribution:
        contribution = find_excerpts(
            body,
            CONTRIBUTION_PATTERNS,
            limit=2,
            exclude=objective,
        )

    future_work = find_excerpts(conclusion, FUTURE_WORK_PATTERNS, limit=3)

    return {
        "objective": objective,
        "problem": problem,
        "method": method,
        "contribution": contribution,
        "future_work": future_work,
    }

def categorize_article(text: str) -> dict:
    """Separa o artigo em regiões aproximadas"""
    body, references = split_references(text)

    abstract = extract_section(body, ["abstract"], fallback="start")
    intro = extract_section(body, ["introduction"], fallback="start")

    method_text = extract_section(
        body,
        [
            "method",
            "methods",
            "methodology",
            "materials and methods",
            "approach",
            "proposed approach",
            "experiment",
            "experiments",
            "experimental setup",
        ],
        fallback="middle",
    )

    future_work = extract_section(
        body,
        ["future work", "future research", "future studies", "future direction", "future directions"],
        fallback="end",
    )

    conclusion = extract_section(
        body,
        ["conclusion", "conclusions", "final remarks"],
        fallback="end",
    )

    return {
        "abstract": abstract,
        "intro_text": intro,
        "method_text": method_text,
        "body_text": body,
        "conclusion_text": conclusion,
        "future_work_text": future_work,
        "references": references,
    }


def extract_article_information(article_name: str, text: str, references: list[str] | None = None) -> dict:
    """Extrai as informações principais de um artigo"""
    text = normalize_text(text)
    paper = categorize_article(text)

    if references is not None:
        paper["references"] = references

    info = extract_info(paper)

    review_notes = []

    if not info["objective"]:
        review_notes.append("Objective not found automatically.")
    if not info["problem"]:
        review_notes.append("Problem not found automatically.")
    if not info["method"]:
        review_notes.append("Method not found automatically.")
    if not info["contribution"]:
        review_notes.append("Contribution not found automatically.")

    return {
        "article": article_name,
        "objective": info["objective"],
        "problem": info["problem"],
        "method": info["method"],
        "contribution": info["contribution"],
        "future_work": info["future_work"],
        "references": paper.get("references", []),
        "review_notes": review_notes,
    }


def extract_information_for_corpus(texts_by_article: Mapping[Path | str, str], references_by_article: Mapping[Path | str, list[str]] | None = None) -> dict[str, dict]:
    """Aplica a extração em todos os artigos"""
    references_by_article = references_by_article or {}
    results = {}

    for article_id, text in texts_by_article.items():
        article_name = Path(str(article_id)).stem

        references = (
            references_by_article.get(article_id)
            or references_by_article.get(str(article_id))
            or references_by_article.get(article_name)
            or []
        )

        results[article_name] = extract_article_information(article_name=article_name, text=text, references=references)

    return results

def extract_corpus(corpus: Mapping[str, dict]) -> dict[str, dict]:
    """Compatibilidade com corpus já categorizado"""
    return {name: extract_info(paper) for name, paper in corpus.items()}