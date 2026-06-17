"""Demo: RAG sem vs com cross-reference (seguir remissões) (~1s).

    python src/demo.py
"""

from __future__ import annotations

from pathlib import Path

from crossref import Retriever, completude, cross_ref, load_artigos, naive

ROOT = Path(__file__).parent.parent

# Cada consulta tem "spans": partes obrigatórias da resposta. Em Q1 e Q2 elas estão
# no artigo citado por remissão; em Q3 estão no próprio artigo (sem remissão).
CONSULTAS = [
    ("Quais os requisitos para ser beneficiario do Programa Alfa?",
     ["beneficiario", "cinquenta alunos", "adesao formal do gestor"]),
    ("Em que meses o repasse e pago?",
     ["duas parcelas", "marco", "agosto"]),
    ("Como e ate quando e feita a prestacao de contas?",
     ["sistema oficial", "trinta dias"]),
]


def main() -> None:
    artigos = load_artigos(ROOT / "data" / "regulamento.json")
    r = Retriever(artigos)

    print("=" * 78)
    print("Cross-reference: seguir as remissões entre dispositivos")
    print("=" * 78)

    soma = {"naive": 0.0, "cross": 0.0}
    for q, spans in CONSULTAS:
        cn = naive(r, q)
        cc = cross_ref(r, q, saltos=1)
        c_naive = completude(cn, spans)
        c_cross = completude(cc, spans)
        soma["naive"] += c_naive
        soma["cross"] += c_cross
        print(f"\nP: {q}")
        print(f"   ingênuo      (completude {c_naive:.0%}): {cn}")
        print(f"   cross-ref    (completude {c_cross:.0%}): {cc}")

    n = len(CONSULTAS)
    print("\n" + "-" * 78)
    print(f"Completude média do contexto: ingênuo {soma['naive']/n:.0%}, "
          f"cross-reference {soma['cross']/n:.0%}")
    print("(cross-reference só acrescenta os artigos citados; nunca remove o top-1)")


if __name__ == "__main__":
    main()
