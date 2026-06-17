import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

from crossref import (  # noqa: E402
    Retriever,
    completude,
    cross_ref,
    load_artigos,
    naive,
    parse_refs,
)

ARTIGOS = load_artigos(ROOT / "data" / "regulamento.json")
R = Retriever(ARTIGOS)

Q_REQ = "Quais os requisitos para ser beneficiario do Programa Alfa?"
SPANS_REQ = ["beneficiario", "cinquenta alunos", "adesao formal do gestor"]
Q_CONTAS = "Como e ate quando e feita a prestacao de contas?"
SPANS_CONTAS = ["sistema oficial", "trinta dias"]


def test_parse_refs_extrai_remissoes():
    assert parse_refs("atende aos requisitos do art. 7.", eu_mesmo=3) == [7]
    assert parse_refs("observado o art. 9 e o art. 12", eu_mesmo=5) == [9, 12]
    assert parse_refs("texto do art. 5 sobre si", eu_mesmo=5) == []  # não conta a si


def test_naive_para_no_artigo_com_remissao():
    ctx = naive(R, Q_REQ)
    assert "art. 7" in ctx
    assert completude(ctx, SPANS_REQ) < 1.0  # não tem os requisitos em si


def test_cross_ref_puxa_o_dispositivo_citado():
    ctx = cross_ref(R, Q_REQ, saltos=1)
    assert completude(ctx, SPANS_REQ) == 1.0
    assert "cinquenta alunos" in ctx


def test_cross_ref_nao_atrapalha_sem_remissao():
    # Artigo auto-suficiente: naive já completa e cross-ref mantém.
    assert completude(naive(R, Q_CONTAS), SPANS_CONTAS) == 1.0
    assert completude(cross_ref(R, Q_CONTAS, 1), SPANS_CONTAS) == 1.0


def test_completude_media_melhora():
    consultas = [
        (Q_REQ, SPANS_REQ),
        ("Em que meses o repasse e pago?", ["duas parcelas", "marco", "agosto"]),
        (Q_CONTAS, SPANS_CONTAS),
    ]
    n = len(consultas)
    media_naive = sum(completude(naive(R, q), s) for q, s in consultas) / n
    media_cross = sum(completude(cross_ref(R, q, 1), s) for q, s in consultas) / n
    assert media_cross > media_naive
    assert media_cross == 1.0
