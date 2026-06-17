# rag-cross-reference

Cross-reference: seguir as **remissões** entre dispositivos como arestas do grafo,
puxando o artigo citado para completar a resposta.

> **Em uma frase:** em texto normativo a resposta quase nunca está num artigo só; o
> art. 3º remete ao art. 7º, e quem não abre o art. 7º responde sem os requisitos.
> Detectar as remissões ("art. N") e puxar os dispositivos citados reconstrói a
> unidade de sentido que a lei deixou distribuída.

> *Cross-reference: legal text is full of pointers ("under art. 7", "subject to
> art. 9"). A flat retriever returns only the article matching the query and stops at
> the pointer. Following the reference and pulling the cited article completes the
> answer. It only adds cited articles; it never drops the top hit.*

---

## O problema

Normas são um grafo de remissões. Um artigo define um conceito e delega a condição a
outro: "considera-se beneficiário a escola que atende aos requisitos do art. 7º". A
busca por similaridade acha o art. 3º (que casa com "beneficiário") e devolve só ele.
O modelo lê "atende aos requisitos do art. 7º" e não tem o art. 7º no contexto, então
responde sem os requisitos, ou pior, inventa. A informação existe no corpus, mas não
chegou ao gerador.

## Como funciona (o técnico)

Cada artigo é um nó. As remissões viram arestas, extraídas do texto por regex.

- `parse_refs(texto)` — acha os números de artigo citados (`art. 7`, `art. 9`), menos
  o próprio.
- `naive(query)` — devolve só o artigo top-1 da similaridade.
- `cross_ref(query, saltos)` — devolve o top-1 **mais** os artigos que ele cita,
  seguindo as arestas por `saltos` níveis (BFS), em ordem do documento.

```
cross_ref(query, saltos):
    inicio = top1_similaridade(query)
    vistos = {inicio}; fronteira = [inicio]
    repita saltos vezes:
        para cada art na fronteira:
            para cada num em parse_refs(art.texto):
                se art[num] não visto: adiciona a vistos e à próxima fronteira
    retorna textos de vistos, ordenados por número de artigo
```

Complexidade: a busca top-1, mais um BFS de profundidade `saltos` sobre arestas
explícitas (poucas por artigo). Sem reindexar, sem modelo extra.

## Resultado (determinístico, offline)

Regulamento fictício do Programa Alfa, com remissões reais entre artigos.

| Consulta                                  | Ingênuo | Cross-reference |
| ----------------------------------------- | ------- | --------------- |
| Requisitos do beneficiário (art. 3→7)     | 33%     | **100%**        |
| Meses do repasse (art. 5→9)               | 33%     | **100%**        |
| Prestação de contas (art. 12, sem remissão) | 100%  | 100%            |
| **Completude média do contexto**          | **56%** | **100%**        |

Quando o artigo é auto-suficiente (sem remissão), o cross-reference mantém 100%: ele
só acrescenta os artigos citados, nunca remove o top-1.

Rode você mesmo:

```bash
pip install -r requirements.txt
python src/demo.py
python -m pytest -q
```

## Como explicar em 30 segundos

"A lei é cheia de 'nos termos do art. tal'. A busca acha o artigo que fala do tema,
mas a regra de verdade está no artigo citado, que ficou de fora. Eu sigo a remissão e
trago também o artigo apontado. A resposta deixa de ser pela metade, e não custa nada
porque a remissão está escrita no texto."

## Cross-reference vs hierarquia vs adjacência

Três sinais estruturais distintos e complementares:

- **Hierarquia** (`graphrag-hierarquia-normativa`): pega o **pai** (caput a partir do inciso).
- **Adjacência** (`rag-chunk-adjacency`): pega os **vizinhos sequenciais** (chunk anterior/seguinte).
- **Cross-reference** (aqui): segue **links explícitos** entre artigos/leis, que podem estar longe no documento.

O `rag-legal-graph-lite` junta os três num grafo só.

## Limitações honestas

- Corpus pequeno e fictício, escolhido para o efeito ser claro e reproduzível.
- O parser de remissões é um regex simples (`art. N`). Remissões reais são bem mais
  variadas: "Lei nº X", "§ 2º do art. 7º", "inciso III", "Capítulo IV", remissão
  relativa ("artigo anterior"). Um parser de produção precisa cobrir esses casos.
- Seguir remissões em cadeia (saltos > 1) pode inflar o contexto; aqui 1 salto basta.
  Em produção, limite a profundidade e o número de nós trazidos.
- A métrica de completude usa presença de spans (substring), proxy de "a informação
  está no contexto", não mede a qualidade da geração.

## Referências científicas (crédito aos autores)

- **Lewis et al. (2020).** *Retrieval-Augmented Generation for Knowledge-Intensive
  NLP Tasks.* NeurIPS.
- **Edge et al. (2024).** *From Local to Global: A Graph RAG Approach to Query-Focused
  Summarization.* arXiv:2404.16130. RAG sobre grafo de relações.
- **Gao et al. (2024).** *Retrieval-Augmented Generation for Large Language Models: A
  Survey.* arXiv:2312.10997.
- Corpus fictício; nenhuma relação com dados reais.

Bibliografia completa do portfólio em `REFERENCIAS.md`.

---

Part of my LinkedIn series on efficient RAG → [Flávia Gaia](https://www.linkedin.com/in/flavia-gaia/)
