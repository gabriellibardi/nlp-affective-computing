import json
import re
from pathlib import Path
from typing import Iterable, Mapping

CONTEXT = {
    "ont": "http://uem-iia-pln.org/ontologia-artigo-cientifico#",
    "Corpus": "ont:Corpus",
    "Artigo": "ont:ArtigoCientifico",
    "id": "ont:identificador",
    "artigos": "ont:temArtigo",
    "objetivo": "ont:temObjetivo",
    "problema": "ont:temProblema",
    "metodologia": "ont:temMetodologia",
    "contribuicao": "ont:temContribuicao",
    "trabalhoFuturo": "ont:temTrabalhoFuturo",
    "referencias": "ont:temReferencia",
    "termoMaisFrequente": "ont:termoMaisFrequente",
    "termo": "ont:termo",
    "frequencia": "ont:frequencia",
    "tokens": "ont:tokens",
}

def _as_list(value: object) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]

def _make_id(article_id: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", article_id).strip("-").lower()
    return f"urn:artigo:{slug}"

def build_jsonld_corpus(extractions: Mapping[str, Mapping], most_common_terms: Iterable[tuple[str, int]] | None = None, tokens_by_article: Mapping[str, list[str]] | None = None) -> dict:
    """Monta o documento JSON-LD do corpus

    Os tokens por artigo são guardados na ontologia para permitir que os gráficos sejam gerados sem reler os PDFs
    """
    tokens_by_article = tokens_by_article or {}
    articles = []

    for article_id, info in extractions.items():
        articles.append(
            {
                "@id": _make_id(article_id),
                "@type": "ArtigoCientifico",
                "identificador": article_id,
                "temObjetivo": _as_list(info.get("objective")),
                "temProblema": _as_list(info.get("problem")),
                "temMetodologia": _as_list(info.get("method")),
                "temContribuicao": _as_list(info.get("contribution")),
                "temTrabalhoFuturo": _as_list(info.get("future_work")),
                "temReferencia": _as_list(info.get("references")),
                "tokens": tokens_by_article.get(article_id, []),
            }
        )

    return {
        "@context": CONTEXT,
        "@type": "Corpus",
        "temArtigo": articles,
        "termoMaisFrequente": [
            {"termo": term, "frequencia": freq} for term, freq in most_common_terms
        ],
    }

def save_jsonld(data: Mapping, output_path: Path | str) -> None:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def ontology_summary(ontology: Mapping) -> str:
    articles = ontology.get("temArtigo", [])
    lines = [
        f"Artigos na ontologia : {len(articles)}",
        f"Termos globais       : {len(ontology.get('termoMaisFrequente', []))}",
    ]

    for article in articles:
        filled = sum(
            1
            for field in [
                "temObjetivo",
                "temProblema",
                "temMetodologia",
                "temContribuicao",
                "temTrabalhoFuturo",
            ]
            if article.get(field)
        )
        lines.append(
            f"  - {article.get('identificador', ''):20s} | "
            f"extração: {filled}/5 campos | "
            f"refs: {len(article.get('temReferencia', []))}"
        )

    return "\n".join(lines)
