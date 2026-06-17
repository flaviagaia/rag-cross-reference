"""Cross-reference: seguir as remissões entre dispositivos como arestas do grafo.

Em texto normativo, a resposta raramente está num artigo só. O art. 3º diz quem é
beneficiário "nos termos do art. 7º"; quem responde sem abrir o art. 7º não sabe os
requisitos. O recuperador ingênuo traz só o artigo que casa com a pergunta. O
cross-reference detecta as remissões ("art. N") no texto recuperado e puxa também os
dispositivos citados, reconstruindo a unidade de sentido distribuída.

- parse_refs   : extrai os números de artigo citados num texto (regex "art. N").
- naive        : devolve só o artigo top-1.
- cross_ref    : devolve o top-1 + os artigos que ele cita (1 salto por padrão).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

_REF = re.compile(r"art\.?\s*(\d+)", re.IGNORECASE)


@dataclass(frozen=True)
class Artigo:
    id: str
    num: int
    rotulo: str
    texto: str


def load_artigos(path: Path) -> list[Artigo]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return [Artigo(**n) for n in data["nodes"]]


def parse_refs(texto: str, eu_mesmo: int | None = None) -> list[int]:
    """Números de artigo citados no texto (sem contar a si mesmo)."""
    nums = [int(m) for m in _REF.findall(texto)]
    return [n for n in nums if n != eu_mesmo]


class Retriever:
    def __init__(self, artigos: list[Artigo]) -> None:
        self.artigos = artigos
        self.por_num = {a.num: a for a in artigos}
        self._vec = TfidfVectorizer(ngram_range=(1, 2), strip_accents="unicode")
        self._mat = self._vec.fit_transform(f"{a.rotulo} {a.texto}" for a in artigos)

    def top(self, query: str) -> Artigo:
        sims = cosine_similarity(self._vec.transform([query]), self._mat).ravel()
        return self.artigos[int(sims.argmax())]


def naive(retriever: Retriever, query: str) -> str:
    """Só o artigo que casa com a pergunta."""
    return retriever.top(query).texto


def cross_ref(retriever: Retriever, query: str, saltos: int = 1) -> str:
    """Top-1 + dispositivos citados (seguindo remissões por 'saltos' níveis)."""
    inicio = retriever.top(query)
    vistos: dict[str, Artigo] = {inicio.id: inicio}
    fronteira = [inicio]
    for _ in range(saltos):
        proxima = []
        for art in fronteira:
            for num in parse_refs(art.texto, eu_mesmo=art.num):
                alvo = retriever.por_num.get(num)
                if alvo and alvo.id not in vistos:
                    vistos[alvo.id] = alvo
                    proxima.append(alvo)
        fronteira = proxima
    # ordem do documento (por num)
    return " ".join(a.texto for a in sorted(vistos.values(), key=lambda a: a.num))


def completude(contexto: str, spans: list[str]) -> float:
    return sum(s in contexto for s in spans) / len(spans)
