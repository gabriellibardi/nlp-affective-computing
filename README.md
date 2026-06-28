# nlp-affective-computing

Sistema para análise textual de artigos científicos sobre **Computação Afetiva**, utilizando técnicas clássicas de Processamento de Linguagem Natural.

O projeto lê artigos em PDF, realiza pré-processamento textual, extrai informações relevantes, constrói uma ontologia em JSON-LD e gera visualizações automáticas a partir dos dados extraídos.

## Como executar

```bash
pip install -r requirements.txt
python -m nltk.downloader stopwords wordnet omw-1.4
python src/main.py
```

## Estrutura de entrada e saída

Os artigos em PDF devem estar na pasta:

```text
data/raw/
```

Durante a execução, o sistema gera arquivos intermediários e resultados finais nas seguintes pastas:

```text
data/processed/       # textos extraídos e limpos dos PDFs
data/no_references/   # textos dos artigos sem a seção de referências
data/ontology/        # ontologia JSON-LD gerada
data/figures/         # gráficos gerados automaticamente
```

O principal arquivo gerado é:

```text
data/ontology/articles_ontology.jsonld
```

## Fluxo principal do sistema

O ponto de entrada do projeto é o arquivo:

```text
src/main.py
```

Ele coordena todo o pipeline de processamento dos artigos. O fluxo geral é:

1. leitura dos PDFs;
2. limpeza do texto extraído;
3. separação entre corpo do artigo e referências;
4. pré-processamento textual;
5. geração de Bag-of-Words;
6. extração de informações dos artigos;
7. construção da ontologia JSON-LD;
8. geração dos gráficos.

## 1. Leitura dos PDFs

O sistema procura automaticamente os arquivos PDF dentro da pasta:

```text
data/raw/
```

Cada PDF é lido e convertido para texto. Em seguida, esse texto passa por uma etapa de limpeza para reduzir ruídos comuns de arquivos PDF.

O texto limpo é salvo em:

```text
data/processed/
```

Essa pasta funciona como cache. Assim, caso o pipeline seja executado novamente, o sistema não precisa extrair e limpar o mesmo PDF outra vez.

## 2. Limpeza e separação de referências

Depois da limpeza inicial, o sistema separa o corpo principal do artigo da seção de referências.

A separação é feita procurando títulos como:

```text
references
bibliography
acm references
literature cited
```

O corpo do artigo, sem as referências, é salvo em:

```text
data/no_references/
```

As referências são armazenadas separadamente para depois serem inseridas na ontologia.

## 3. Pré-processamento textual

O corpo de cada artigo passa por técnicas clássicas de PLN:

* tokenização;
* remoção de stopwords;
* lematização.

A tokenização divide o texto em unidades menores, chamadas tokens.

A remoção de stopwords remove palavras muito comuns, como artigos, preposições e conectivos.

A lematização reduz palavras para uma forma base. Por exemplo, termos flexionados podem ser tratados de forma mais uniforme.

Esse processo utiliza recursos do NLTK:

```text
stopwords
wordnet
omw-1.4
```

Os tokens resultantes são usados para gerar os termos frequentes, os gráficos e a ontologia.

## 4. Bag-of-Words

Após o pré-processamento, o sistema monta uma representação Bag-of-Words.

Essa representação conta a frequência dos termos no corpus, sem considerar a ordem original das palavras.

A partir dela, são obtidos os termos mais frequentes do conjunto de artigos.

Esses termos são armazenados na ontologia no campo:

```text
termoMaisFrequente
```

Cada termo é salvo com sua respectiva frequência:

```json
{
  "termo": "emotion",
  "frequencia": 1376
}
```

## 5. Extração de informações

A etapa de extração está implementada no arquivo:

```text
src/extraction.py
```

Essa etapa não utiliza modelos pré-treinados nem algoritmos de aprendizado de máquina. A extração é feita por heurísticas, expressões regulares e padrões textuais.

O processo funciona assim:

1. o artigo é dividido em regiões aproximadas;
2. o texto é dividido em frases;
3. cada frase é comparada com padrões pré-definidos;
4. os trechos encontrados são associados aos campos da ontologia.

As principais regiões consideradas são:

```text
abstract
introduction
method
results
discussion
conclusion
references
```

Os principais campos extraídos são:

```text
objective
problem
method
contribution
future_work
references
```

## 6. Objetivo

O campo de objetivo tenta identificar o propósito principal do artigo.

O sistema procura padrões como:

```text
the objective of this paper is
the aim of this study is
this paper aims to
we aim to
in this paper, we
```

O resultado é armazenado na ontologia como:

```text
temObjetivo
```

## 7. Problema

O campo de problema busca identificar a motivação, lacuna ou dificuldade abordada pelo artigo.

São buscados termos como:

```text
problem
challenge
gap
limitation
lack of
there is a need
remains unclear
```

O resultado é armazenado como:

```text
temProblema
```

## 8. Metodologia

O campo de metodologia tenta identificar como o estudo foi conduzido.

O sistema procura termos relacionados a métodos, experimentos, datasets e participantes, como:

```text
method
approach
framework
dataset
experiment
participants
survey
we conducted
we collected
we evaluated
```

O resultado é armazenado como:

```text
temMetodologia
```

## 9. Contribuição

O campo de contribuição busca identificar o que o artigo propõe ou adiciona à área.

São procurados padrões como:

```text
we contribute
we propose
we present
we introduce
we provide
this paper proposes
```

O resultado é armazenado como:

```text
temContribuicao
```

## 10. Trabalhos futuros

O campo de trabalhos futuros tenta identificar sugestões de continuidade da pesquisa.

O sistema procura expressões como:

```text
future work
future research
future studies
future direction
we plan to
we intend to
```

Esse campo pode ficar vazio em alguns artigos, pois nem todo artigo possui uma seção explícita de trabalhos futuros.

O resultado é armazenado como:

```text
temTrabalhoFuturo
```

## 11. Referências

As referências são extraídas a partir da seção final do artigo.

O sistema tenta remover marcadores como:

```text
[1]
[2]
1.
2.
```

As referências extraídas são armazenadas como:

```text
temReferencia
```

## 12. Construção da ontologia JSON-LD

A ontologia é construída no arquivo:

```text
src/ontology.py
```

Ela representa o corpus analisado e os artigos extraídos em formato JSON-LD.

A ontologia contém:

* corpus;
* artigos;
* identificador de cada artigo;
* objetivo;
* problema;
* metodologia;
* contribuição;
* trabalhos futuros;
* referências;
* tokens;
* termos mais frequentes.

A ontologia utiliza o namespace:

```text
http://uem-iia-pln.org/ontologia-artigo-cientifico#
```

Um artigo na ontologia segue uma estrutura semelhante a:

```json
{
  "@id": "urn:artigo:3449151",
  "@type": "ArtigoCientifico",
  "identificador": "3449151",
  "temObjetivo": [],
  "temProblema": [],
  "temMetodologia": [],
  "temContribuicao": [],
  "temTrabalhoFuturo": [],
  "temReferencia": [],
  "tokens": []
}
```

## 13. Geração de visualizações

As visualizações são geradas no arquivo:

```text
src/visualization.py
```

Esse módulo utiliza apenas a ontologia JSON-LD já gerada. Ou seja, ele não relê os PDFs.

Os gráficos são salvos em:

```text
data/figures/
```

## Gráficos gerados

### Top 10 termos mais frequentes

Mostra os 10 termos mais frequentes no corpus.

Arquivo gerado:

```text
1_top_10_termos.png
```

### Nuvem de palavras geral

Mostra uma visualização geral dos termos mais recorrentes nos artigos.

Arquivo gerado:

```text
2_nuvem_palavras_geral.png
```

### Heatmap artigo × termo

Mostra como os termos mais frequentes se distribuem entre os artigos.

Arquivo gerado:

```text
3_heatmap_artigo_por_termo.png
```

### Heatmap de técnicas por artigo

Mostra a presença de técnicas e conceitos relacionados à Computação Afetiva em cada artigo.

Algumas técnicas verificadas são:

```text
affective computing
emotion recognition
sentiment analysis
facial expression
physiological signal
eye tracking
valence
arousal
eeg
ecg
```

Arquivo gerado:

```text
4_heatmap_tecnica_por_artigo.png
```

### Similaridade entre artigos

Calcula a similaridade entre os artigos usando o índice de Jaccard sobre os conjuntos de tokens.

A fórmula geral é:

```text
interseção dos tokens / união dos tokens
```

Arquivo gerado:

```text
5_heatmap_similaridade_artigos.png
```

### Termos em trabalhos futuros

Mostra os termos mais frequentes encontrados nos trechos extraídos de trabalhos futuros.

Antes da contagem, o sistema remove stopwords e termos genéricos.

Arquivo gerado:

```text
6_top_10_trabalhos_futuros.png
```

### Cobertura da extração

Mostra quantos artigos tiveram cada campo extraído com sucesso.

Os campos analisados são:

```text
objetivo
problema
metodologia
contribuição
trabalho futuro
referência
```

Arquivo gerado:

```text
7_cobertura_extracao.png
```

## Técnicas utilizadas

O projeto utiliza técnicas clássicas de PLN e processamento textual:

* extração de texto de PDFs;
* limpeza textual;
* segmentação em frases;
* tokenização;
* remoção de stopwords;
* lematização;
* Bag-of-Words;
* n-gramas;
* extração baseada em regras;
* expressões regulares;
* geração de ontologia JSON-LD;
* contagem de frequência;
* nuvem de palavras;
* heatmaps;
* similaridade de Jaccard.

## Observações

A abordagem utilizada é baseada em regras. Isso torna o sistema mais simples, transparente e fácil de explicar.

Como os artigos estão em PDF, ainda podem aparecer ruídos no texto extraído, como cabeçalhos, rodapés, numeração de páginas, informações de copyright e metadados editoriais.

O sistema possui filtros para reduzir esses ruídos, mas a qualidade da extração depende da qualidade do texto obtido a partir dos PDFs.

## Resultado final

Ao final da execução, os principais resultados gerados são:

```text
data/ontology/articles_ontology.jsonld
data/figures/*.png
```

A ontologia armazena os dados estruturados extraídos dos artigos, enquanto os gráficos apresentam uma visão visual do corpus analisado.