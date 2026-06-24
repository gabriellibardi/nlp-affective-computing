"""
Extraction rules for Step 2 of the scientific article analysis work.

This module extracts candidate excerpts for:
- objective
- problem
- method / methodology
- contribution

The implementation is intentionally based on regular expressions and simple
heuristics, without pretrained models or machine learning libraries.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Mapping

@dataclass
class ExtractedArticleInfo:
    """
    Information extracted from one scientific article.

    The fields are lists because an article may contain more than one good
    candidate sentence for the same category.
    """

    article: str
    objective: list[str]
    problem: list[str]
    method: list[str]
    contribution: list[str]
    review_notes: list[str]


# ---------------------------------------------------------------------------
# Text normalization and sentence handling
# ---------------------------------------------------------------------------

def normalize_spaces(text: str) -> str:
    """
    Normalize whitespace produced during PDF extraction.
    """
    return re.sub(r"\s+", " ", text or "").strip()


def split_sentences(text: str) -> list[str]:
    """
    Split text into sentences using a lightweight regex heuristic.

    This avoids depending on sentence tokenizers or pretrained NLP models.
    It is not perfect, but works reasonably well for scientific articles.
    """
    text = normalize_spaces(text)

    if not text:
        return []

    raw_sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'])", text)
    sentences: list[str] = []

    for sentence in raw_sentences:
        sentence = sentence.strip()

        # Very short strings are usually headings, captions or extraction noise.
        if len(sentence) < 45:
            continue

        # Very long strings usually indicate that the PDF extraction merged
        # multiple sections into one sentence.
        if len(sentence) > 900:
            continue

        sentences.append(sentence)

    return sentences


def sentence_terms(sentence: str) -> set[str]:
    """
    Return relevant lowercase terms from a sentence.
    """
    return set(re.findall(r"[a-zA-Z]{3,}", sentence.lower()))


def jaccard_similarity(a: str, b: str) -> float:
    """
    Compare two sentences using Jaccard similarity over word sets.
    """
    terms_a = sentence_terms(a)
    terms_b = sentence_terms(b)

    if not terms_a or not terms_b:
        return 0.0

    return len(terms_a & terms_b) / len(terms_a | terms_b)


def append_if_unique(
    selected: list[str],
    candidate: str,
    limit: int,
    similarity_threshold: float = 0.62,
) -> None:
    """
    Append a sentence only if it is not too similar to selected sentences.
    """
    if len(selected) >= limit:
        return

    for sentence in selected:
        if jaccard_similarity(sentence, candidate) >= similarity_threshold:
            return

    selected.append(candidate)


# ---------------------------------------------------------------------------
# Section detection
# ---------------------------------------------------------------------------

INTRODUCTION_HEADINGS = [
    "introduction",
]

METHOD_HEADINGS = [
    "method",
    "methods",
    "methodology",
    "materials and methods",
    "approach",
    "proposed approach",
    "proposed method",
    "study design",
    "experimental setup",
    "experiment",
    "experiments",
]

CONCLUSION_HEADINGS = [
    "discussion",
    "conclusion",
    "conclusions",
    "final remarks",
]

COMMON_NEXT_HEADINGS = [
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
    "proposed method",
    "study design",
    "experimental setup",
    "experiment",
    "experiments",
    "results",
    "findings",
    "discussion",
    "evaluation",
    "limitations",
    "conclusion",
    "conclusions",
    "acknowledgements",
    "acknowledgments",
    "references",
    "bibliography",
]


def _heading_regex(headings: Iterable[str]) -> str:
    """
    Build a regex that finds section titles with optional numbering.
    """
    escaped = [re.escape(h) for h in headings]

    return (
        r"(?:^|\s)"
        r"(?:\d+(?:\.\d+)*\.?\s*)?"
        r"("
        + "|".join(escaped)
        + r")"
        r"(?:\s|$|[:.])"
    )


def find_heading(text: str, headings: Iterable[str], start: int = 0) -> re.Match[str] | None:
    """
    Find the first heading occurrence after a given position.
    """
    return re.search(_heading_regex(headings), text[start:], flags=re.IGNORECASE)


def extract_region(
    text: str,
    start_headings: list[str],
    end_headings: list[str],
    fallback: str,
) -> str:
    """
    Extract an approximate region from an article.

    fallback options:
    - "start": first third of the text
    - "middle": whole text
    - "end": last third of the text
    """
    text = normalize_spaces(text)

    start_match = find_heading(text, start_headings)

    if start_match:
        start_position = start_match.start()
        search_from = min(len(text), start_position + 80)

        end_match = find_heading(text, end_headings, start=search_from)

        if end_match:
            end_position = search_from + end_match.start()

            if end_position > start_position:
                return text[start_position:end_position].strip()

        return text[start_position:].strip()

    if fallback == "start":
        return text[: int(len(text) * 0.35)]

    if fallback == "end":
        return text[int(len(text) * 0.65):]

    return text


# ---------------------------------------------------------------------------
# Extraction patterns
# ---------------------------------------------------------------------------

OBJECTIVE_PATTERNS = [
    (r"\bthe objective of (this|the) (paper|article|study|work|research) is\b", 10),
    (r"\bthe aim of (this|the) (paper|article|study|work|research) is\b", 10),
    (r"\bthe goal of (this|the) (paper|article|study|work|research) is\b", 9),
    (r"\bthe purpose of (this|the) (paper|article|study|work|research) is\b", 9),
    (r"\bthis (paper|article|study|work|research) aims to\b", 9),
    (r"\bthis (paper|article|study|work|research) seeks to\b", 8),
    (r"\bthis (paper|article|study|work|research) investigates\b", 7),
    (r"\bthis (paper|article|study|work|research) explores\b", 7),
    (r"\bin this (paper|article|study|work|research), we\b", 5),
    (r"\bwe aim to\b", 8),
    (r"\bwe seek to\b", 8),
    (r"\bwe investigate\b", 7),
    (r"\bwe examine\b", 7),
    (r"\bwe explore\b", 7),
    (r"\bwe analyze\b", 6),
    (r"\bwe analyse\b", 6),
]

PROBLEM_PATTERNS = [
    (r"\bresearch problem\b", 10),
    (r"\bproblem\b", 7),
    (r"\bchallenge\b", 7),
    (r"\bchallenges\b", 7),
    (r"\bgap\b", 7),
    (r"\bgaps\b", 7),
    (r"\blimitation\b", 6),
    (r"\blimitations\b", 6),
    (r"\black of\b", 7),
    (r"\blacks\b", 6),
    (r"\bthere is a need\b", 8),
    (r"\bthere remains\b", 6),
    (r"\bremains unclear\b", 8),
    (r"\blittle is known\b", 8),
    (r"\bnot well understood\b", 8),
    (r"\bis difficult\b", 5),
    (r"\bare difficult\b", 5),
    (r"\bexisting (methods|approaches|studies|systems|solutions)\b", 4),
    (r"\bhowever\b", 2),
    (r"\bdespite\b", 2),
]

METHOD_PATTERNS = [
    (r"\bmethod\b", 5),
    (r"\bmethods\b", 5),
    (r"\bmethodology\b", 8),
    (r"\bapproach\b", 5),
    (r"\bframework\b", 5),
    (r"\btechnique\b", 4),
    (r"\balgorithm\b", 4),
    (r"\bexperiment\b", 6),
    (r"\bexperiments\b", 6),
    (r"\bexperimental\b", 5),
    (r"\bevaluation\b", 4),
    (r"\bdataset\b", 6),
    (r"\bcorpus\b", 6),
    (r"\bparticipants\b", 6),
    (r"\bquestionnaire\b", 7),
    (r"\bsurvey\b", 7),
    (r"\binterview\b", 7),
    (r"\binterviews\b", 7),
    (r"\bcontent analysis\b", 8),
    (r"\bcase study\b", 7),
    (r"\bwe conducted\b", 8),
    (r"\bwe collected\b", 7),
    (r"\bwe used\b", 6),
    (r"\bwe designed\b", 6),
    (r"\bwe developed\b", 6),
    (r"\bwe implemented\b", 6),
]

CONTRIBUTION_PATTERNS = [
    (r"\bcontributes to\b", 10),
    (r"\bcontribute to\b", 10),
    (r"\bcontribution\b", 9),
    (r"\bcontributions\b", 9),
    (r"\bmain contribution\b", 10),
    (r"\bmain contributions\b", 10),
    (r"\bwe contribute\b", 10),
    (r"\bthis (paper|article|study|work|research) contributes\b", 10),
    (r"\bthe contributions of (this|the) (paper|article|study|work|research)\b", 10),
    (r"\bwe make the following contributions\b", 11),
    (r"\bour findings\b", 5),
    (r"\bour results\b", 4),
    (r"\bwe provide\b", 5),
    (r"\bwe offer\b", 5),
    (r"\bwe demonstrate\b", 5),
    (r"\bwe show\b", 4),
    (r"\bnovel\b", 4),
    (r"\bfor the first time\b", 6),
]

AFFECTIVE_COMPUTING_BONUS = [
    r"\baffective computing\b",
    r"\bemotion recognition\b",
    r"\bemotion detection\b",
    r"\bemotion classification\b",
    r"\bsentiment analysis\b",
    r"\bfacial expression\b",
    r"\bvalence\b",
    r"\barousal\b",
    r"\bphysiological signal",
    r"\beeg\b",
    r"\becg\b",
    r"\bgaze\b",
    r"\bmultimodal\b",
    r"\bhuman-computer interaction\b",
    r"\bhci\b",
]


# ---------------------------------------------------------------------------
# Scoring and extraction
# ---------------------------------------------------------------------------

def score_sentence(
    sentence: str,
    patterns: list[tuple[str, int]],
    bonus_patterns: list[str] | None = None,
) -> int:
    """
    Score a sentence according to category patterns.
    """
    score = 0

    for pattern, weight in patterns:
        if re.search(pattern, sentence, flags=re.IGNORECASE):
            score += weight

    if bonus_patterns:
        for pattern in bonus_patterns:
            if re.search(pattern, sentence, flags=re.IGNORECASE):
                score += 2

    return score


def select_candidate_sentences(
    text: str,
    patterns: list[tuple[str, int]],
    limit: int,
    bonus_patterns: list[str] | None = None,
    forbidden: list[str] | None = None,
) -> list[str]:
    """
    Select the highest scoring non-duplicated candidate sentences.
    """
    forbidden = forbidden or []
    candidates: list[tuple[int, str]] = []

    for sentence in split_sentences(text):
        if any(jaccard_similarity(sentence, blocked) >= 0.62 for blocked in forbidden):
            continue

        score = score_sentence(sentence, patterns, bonus_patterns)

        if score > 0:
            candidates.append((score, sentence))

    candidates.sort(key=lambda item: item[0], reverse=True)

    selected: list[str] = []

    for _, sentence in candidates:
        append_if_unique(selected, sentence, limit)

    return selected


def extract_article_information(article_name: str, text: str) -> ExtractedArticleInfo:
    """
    Extract Step 2 information from one article text.
    """
    text = normalize_spaces(text)

    introduction_text = extract_region(
        text=text,
        start_headings=INTRODUCTION_HEADINGS,
        end_headings=COMMON_NEXT_HEADINGS,
        fallback="start",
    )

    method_text = extract_region(
        text=text,
        start_headings=METHOD_HEADINGS,
        end_headings=[
            "results",
            "findings",
            "discussion",
            "evaluation",
            "limitations",
            "conclusion",
            "conclusions",
        ],
        fallback="middle",
    )

    conclusion_text = extract_region(
        text=text,
        start_headings=CONCLUSION_HEADINGS,
        end_headings=["references", "bibliography"],
        fallback="end",
    )

    objective = select_candidate_sentences(
        text=introduction_text,
        patterns=OBJECTIVE_PATTERNS,
        limit=3,
        bonus_patterns=AFFECTIVE_COMPUTING_BONUS,
    )

    problem = select_candidate_sentences(
        text=introduction_text,
        patterns=PROBLEM_PATTERNS,
        limit=3,
        bonus_patterns=AFFECTIVE_COMPUTING_BONUS,
    )

    method = select_candidate_sentences(
        text=method_text,
        patterns=METHOD_PATTERNS,
        limit=3,
        bonus_patterns=AFFECTIVE_COMPUTING_BONUS,
    )

    # Contributions often appear in the introduction and conclusion.
    # We also block sentences already selected as objectives, because the work
    # asks to distinguish contribution from objective.
    contribution_text = f"{introduction_text} {conclusion_text}"

    contribution = select_candidate_sentences(
        text=contribution_text,
        patterns=CONTRIBUTION_PATTERNS,
        limit=4,
        bonus_patterns=AFFECTIVE_COMPUTING_BONUS,
        forbidden=objective,
    )

    review_notes: list[str] = []

    if not objective:
        review_notes.append("Objective not found automatically.")

    if not problem:
        review_notes.append("Problem or research gap not found automatically.")

    if not method:
        review_notes.append("Method or methodology not found automatically.")

    if not contribution:
        review_notes.append("Contribution not found automatically.")

    return ExtractedArticleInfo(
        article=article_name,
        objective=objective,
        problem=problem,
        method=method,
        contribution=contribution,
        review_notes=review_notes,
    )


def extract_information_for_corpus(texts_by_article: Mapping[Path | str, str]) -> dict[str, dict]:
    """
    Extract Step 2 information for multiple articles.

    The input should be a dictionary where the key is a Path or article name
    and the value is the article text without references.
    """
    results: dict[str, dict] = {}

    for article_id, text in texts_by_article.items():
        if isinstance(article_id, Path):
            article_name = article_id.stem
        else:
            article_name = Path(str(article_id)).stem

        extraction = extract_article_information(article_name, text)
        results[article_name] = asdict(extraction)

    return results
