from __future__ import annotations

from uuid import uuid4

from app.models import DefasagemRiskRecord
from app.repositories import DefasagemRiskRecordRepository, DomainRepository


class ScalarResultStub:
    def __init__(self, values):
        self.values = values

    def unique(self):
        return self

    def __iter__(self):
        return iter(self.values)


class SessionStub:
    def __init__(self) -> None:
        self.added = None
        self.flushed = False
        self.scalar_value = None
        self.get_value = None

    def scalars(self, statement):
        return ScalarResultStub(["field"])

    def scalar(self, statement):
        return self.scalar_value

    def add(self, value) -> None:
        self.added = value

    def flush(self) -> None:
        self.flushed = True

    def get(self, model, identifier):
        return self.get_value


def test_domain_repository_executes_list_and_item_queries() -> None:
    session = SessionStub()
    repository = DomainRepository(session)

    assert repository.list_active_with_options() == ["field"]
    assert repository.get_active_by_name("sexo_biologico") is None


def test_record_repository_adds_flushes_and_reads() -> None:
    session = SessionStub()
    repository = DefasagemRiskRecordRepository(session)
    values = {
        "defasagem": 1,
        "fase_ordem": 3,
        "idade": 10,
        "ano_ingresso": 2020,
        "ida": 7.8,
        "ieg": 8.2,
        "iaa": 6.5,
        "ips": 9.1,
        "ipv": 7.3,
        "inde": 8.0,
        "genero": "masculino",
        "instituicao": "publica",
        "probabilidade": 0.75,
        "faixa_risco": "alto",
        "acao_sugerida": "Intervenção imediata",
    }

    record = repository.add(values)
    session.get_value = record

    assert isinstance(record, DefasagemRiskRecord)
    assert session.added is record
    assert session.flushed is True
    assert repository.get_by_id(uuid4()) is record


def test_record_repository_lists_all() -> None:
    repository = DefasagemRiskRecordRepository(SessionStub())

    assert repository.list_all() == ["field"]
