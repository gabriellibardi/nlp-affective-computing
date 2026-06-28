"""
Geração de visualizações a partir da ontologia JSON-LD.

Este arquivo usa  data/ontology/articles_ontology.jsonld gerado pela main.py
"""
import argparse
import json
import re
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
from wordcloud import WordCloud

TOKEN_RE = re.compile(r"[a-zA-Z]{3,}")

AFFECTIVE_TECHNIQUES = [
    "affective computing",
    "emotion recognition",
    "emotion detection",
    "emotion classification",
    "sentiment analysis",
    "facial expression",
    "speech emotion",
    "multimodal emotion",
    "physiological signal",
    "human computer interaction",
    "eye tracking",
    "gaze tracking",
    "valence",
    "arousal",
    "eeg",
    "ecg",
]

FUTURE_WORK_STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "into", "onto",
    "are", "was", "were", "has", "have", "had", "not", "but", "can",
    "could", "would", "should", "may", "might", "will", "shall",
    "our", "their", "its", "his", "her", "they", "them", "these", "those",
    "than", "then", "there", "where", "when", "what", "which", "who",
    "how", "why", "such", "also", "more", "most", "some", "any",
    "each", "other", "another", "between", "within", "without",
    "one", "two", "both", "all", "been", "being", "because",
    "future", "work", "research", "study", "studies", "paper", "article",
    "section", "result", "results", "approach", "method", "methods",
    "described", "related", "discussed", "presented", "proposed", "developed",
}

# Leitura da ontologia

def load_ontology(path: str | Path) -> dict:
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Ontologia não encontrada: {path}")

    return json.loads(path.read_text(encoding="utf-8"))


def get_articles(ontology: dict) -> list[dict]:
    articles = ontology.get("temArtigo", [])
    return articles if isinstance(articles, list) else []


def as_list(value) -> list[str]:
    if value is None:
        return []

    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]

    value = str(value).strip()
    return [value] if value else []


def get_article_id(article: dict) -> str:
    return str(article.get("identificador", "sem_id"))


def get_article_year(article: dict) -> str:
    year = str(article.get("ano", "")).strip()
    return year if re.fullmatch(r"\d{4}", year) else "Unknown"


def get_article_tokens(article: dict) -> list[str]:
    tokens = article.get("tokens", [])

    if isinstance(tokens, list) and tokens:
        return [str(t).lower() for t in tokens if str(t).strip()]

    # fallback caso a ontologia antiga não tenha tokens
    text_parts = []
    for field in [
        "titulo",
        "temObjetivo",
        "temProblema",
        "temMetodologia",
        "temContribuicao",
        "temTrabalhoFuturo",
    ]:
        text_parts.extend(as_list(article.get(field)))

    text = " ".join(text_parts).lower()
    return TOKEN_RE.findall(text)


def get_all_tokens(articles: list[dict]) -> list[str]:
    all_tokens = []

    for article in articles:
        all_tokens.extend(get_article_tokens(article))

    return all_tokens


def get_frequency_field(ontology: dict, field_name: str) -> list[tuple[str, int]]:
    raw_items = ontology.get(field_name, [])
    result = []

    if not isinstance(raw_items, list):
        return []

    for item in raw_items:
        if not isinstance(item, dict):
            continue

        term = str(item.get("termo", "")).strip().lower()

        try:
            frequency = int(item.get("frequencia", 0))
        except Exception:
            frequency = 0

        if term and frequency > 0:
            result.append((term, frequency))

    result.sort(key=lambda x: x[1], reverse=True)
    return result


def make_ngrams(tokens: list[str], n: int) -> Counter:
    counter = Counter()

    for i in range(len(tokens) - n + 1):
        gram_tokens = tokens[i:i + n]

        if len(set(gram_tokens)) > 1:
            counter[" ".join(gram_tokens)] += 1

    return counter


# Funções auxiliares de gráfico

def save_empty_plot(output_path: Path, title: str, message: str) -> Path:
    plt.figure(figsize=(10, 6))
    plt.title(title)
    plt.text(0.5, 0.5, message, ha="center", va="center", fontsize=12)
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()

    return output_path


def save_vertical_bar(
    items: list[tuple[str, int]],
    output_path: Path,
    title: str,
    ylabel: str = "Frequência",
) -> Path:
    if not items:
        return save_empty_plot(output_path, title, "Sem dados suficientes")

    labels, values = zip(*items)

    plt.figure(figsize=(11, 6))
    plt.bar(labels, values)
    plt.title(title)
    plt.ylabel(ylabel)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()

    return output_path


def save_heatmap(
    matrix: list[list[int | float]],
    x_labels: list[str],
    y_labels: list[str],
    output_path: Path,
    title: str,
    colorbar_label: str,
) -> Path:
    if not matrix or not x_labels or not y_labels:
        return save_empty_plot(output_path, title, "Sem dados suficientes")

    height = max(6, len(y_labels) * 0.6)
    width = max(10, len(x_labels) * 0.9)

    plt.figure(figsize=(width, height))
    plt.imshow(matrix, aspect="auto")
    plt.colorbar(label=colorbar_label)

    plt.title(title)
    plt.xticks(range(len(x_labels)), x_labels, rotation=45, ha="right")
    plt.yticks(range(len(y_labels)), y_labels)

    for i, row in enumerate(matrix):
        for j, value in enumerate(row):
            text = f"{value:.2f}" if isinstance(value, float) and value % 1 else str(int(value))
            plt.text(j, i, text, ha="center", va="center", fontsize=8)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()

    return output_path

# Gráficos

def plot_top_terms(ontology: dict, articles: list[dict], output_dir: Path) -> Path:
    items = get_frequency_field(ontology, "termoMaisFrequente")

    if not items:
        items = Counter(get_all_tokens(articles)).most_common(10)
    else:
        items = items[:10]

    return save_vertical_bar(
        items,
        output_dir / "1_top_10_termos.png",
        "Top 10 termos mais frequentes",
    )

def plot_wordcloud(ontology: dict, articles: list[dict], output_dir: Path) -> Path:
    output_path = output_dir / "2_nuvem_palavras_geral.png"
    
    items = Counter(get_all_tokens(articles)).most_common(50)

    if not items:
        return save_empty_plot(output_path, "Nuvem de palavras geral", "Sem dados suficientes")

    wordcloud = WordCloud(width=1000, height=500, background_color="white")
    wordcloud.generate_from_frequencies(dict(items))

    plt.figure(figsize=(12, 6))
    plt.imshow(wordcloud, interpolation="bilinear")
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()

    return output_path


def plot_article_term_heatmap(ontology: dict, articles: list[dict], output_dir: Path) -> Path:
    """
    Heatmap artigo × termo
    Mostra a frequência dos principais termos em cada artigo
    """
    top_terms = [term for term, _ in get_frequency_field(ontology, "termoMaisFrequente")[:10]]

    if not top_terms:
        top_terms = [term for term, _ in Counter(get_all_tokens(articles)).most_common(10)]

    article_labels = [get_article_id(article) for article in articles]

    if not articles or not top_terms:
        return save_empty_plot(
            output_dir / "3_heatmap_artigo_por_termo.png",
            "Matriz artigo × termo",
            "Sem dados suficientes",
        )

    matrix = []

    for article in articles:
        counter = Counter(get_article_tokens(article))
        row = [counter[term] for term in top_terms]
        matrix.append(row)

    return save_heatmap(
        matrix,
        top_terms,
        article_labels,
        output_dir / "3_heatmap_artigo_por_termo.png",
        "Matriz de frequência: artigo × termo",
        "Frequência",
    )

def plot_technique_article_heatmap(articles: list[dict], output_dir: Path) -> Path:
    article_labels = [get_article_id(article) for article in articles]
    techniques = AFFECTIVE_TECHNIQUES[:10]

    matrix = []

    for article in articles:
        text = " ".join(get_article_tokens(article)).lower()
        row = []

        for technique in techniques:
            row.append(1 if technique in text else 0)

        matrix.append(row)

    return save_heatmap(
        matrix,
        techniques,
        article_labels,
        output_dir / "4_heatmap_tecnica_por_artigo.png",
        "Presença de técnicas por artigo",
        "Presença",
    )


def plot_article_similarity_heatmap(articles: list[dict], output_dir: Path) -> Path:
    labels = [get_article_id(article) for article in articles]
    token_sets = [set(get_article_tokens(article)) for article in articles]

    if not labels:
        return save_empty_plot(
            output_dir / "5_heatmap_similaridade_artigos.png",
            "Similaridade entre artigos",
            "Sem artigos na ontologia",
        )

    matrix = []

    for set_a in token_sets:
        row = []

        for set_b in token_sets:
            if not set_a or not set_b:
                row.append(0.0)
            else:
                row.append(len(set_a & set_b) / len(set_a | set_b))

        matrix.append(row)

    return save_heatmap(
        matrix,
        labels,
        labels,
        output_dir / "5_heatmap_similaridade_artigos.png",
        "Similaridade entre artigos por tokens",
        "Jaccard",
    )

def plot_future_work_terms(articles: list[dict], output_dir: Path) -> Path:
    tokens = []

    for article in articles:
        future_texts = as_list(article.get("temTrabalhoFuturo"))

        for text in future_texts:
            raw_tokens = TOKEN_RE.findall(text.lower())

            clean_tokens = [
                token
                for token in raw_tokens
                if token not in FUTURE_WORK_STOPWORDS and len(token) > 2
            ]

            tokens.extend(clean_tokens)

    items = Counter(tokens).most_common(10)

    return save_vertical_bar(
        items,
        output_dir / "6_top_10_trabalhos_futuros.png",
        "Top 10 termos em trabalhos futuros",
    )

def plot_extraction_coverage(articles: list[dict], output_dir: Path) -> Path:
    fields = [
        ("temObjetivo", "Objetivo"),
        ("temProblema", "Problema"),
        ("temMetodologia", "Metodologia"),
        ("temContribuicao", "Contribuição"),
        ("temTrabalhoFuturo", "Trabalho futuro"),
        ("temReferencia", "Referência"),
    ]

    items = []

    for field, label in fields:
        count = sum(1 for article in articles if as_list(article.get(field)))
        items.append((label, count))

    return save_vertical_bar(
        items,
        output_dir / "7_cobertura_extracao.png",
        "Quantidade de artigos com cada campo extraído",
        ylabel="Quantidade de artigos",
    )

# Função principal

def generate_all_visualizations(ontology_path: str | Path = "data/ontology/articles_ontology.jsonld", output_dir: str | Path = "data/figures") -> list[Path]:
    """
    Gera todos os gráficos a partir da ontologia JSON-LD.
    """
    ontology_path = Path(ontology_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    ontology = load_ontology(ontology_path)
    articles = get_articles(ontology)

    generated = [
        plot_top_terms(ontology, articles, output_dir),
        plot_wordcloud(ontology, articles, output_dir),
        plot_article_term_heatmap(ontology, articles, output_dir),
        plot_technique_article_heatmap(articles, output_dir),
        plot_article_similarity_heatmap(articles, output_dir),
        plot_future_work_terms(articles, output_dir),
        plot_extraction_coverage(articles, output_dir),
    ]

    return generated


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ontology", default="data/ontology/articles_ontology.jsonld", help="Caminho para a ontologia JSON-LD")
    parser.add_argument("--saida_dir", default="data/figures", help="Diretório onde os gráficos serão salvos")

    args = parser.parse_args()

    generated = generate_all_visualizations(ontology_path=args.ontology, output_dir=args.saida_dir)

    print("Gráficos gerados:")
    for path in generated:
        print(f"- {path}")


if __name__ == "__main__":
    main()