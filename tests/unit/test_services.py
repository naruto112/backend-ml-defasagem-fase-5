from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.services import (
    DefasagemRiskRecordNotFoundError,
    DefasagemRiskRecordService,
    DomainNotFoundError,
    DomainService,
)


class DomainRepositoryStub:
    def __init__(self, fields: list[SimpleNamespace]) -> None:
        self.fields = fields

    def list_active_with_options(self):
        return self.fields

    def get_active_by_name(self, name: str):
        return next((field for field in self.fields if field.name == name), None)


class RecordRepositoryStub:
    def __init__(self, record=None, error: Exception | None = None, records=None) -> None:
        self.record = record
        self.error = error
        self.added = None
        self.records = records or []

    def add(self, values):
        if self.error is not None:
            raise self.error
        self.added = values
        return self.record

    def get_by_id(self, record_id):
        return self.record

    def list_all(self):
        return self.records


class TransactionStub:
    def __init__(self) -> None:
        self.commits = 0
        self.rollbacks = 0

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1


class PredictorStub:
    def __init__(self, result: dict | None = None, error: Exception | None = None) -> None:
        self.result = result or {
            "probabilidade": 0.1,
            "faixa_risco": "Baixo",
            "acao_sugerida": "Sem sinal de alerta",
        }
        self.error = error
        self.called_with = None

    def predict(self, command):
        self.called_with = command
        if self.error is not None:
            raise self.error
        return self.result


def test_domain_service_orders_and_converts_integer_options() -> None:
    field = SimpleNamespace(
        name="sexo_biologico",
        label="Sexo biologico",
        data_type="integer",
        required=True,
        options=[SimpleNamespace(value="1", label="Masculino", display_order=1)],
    )
    service = DomainService(DomainRepositoryStub([field]))  # type: ignore[arg-type]

    result = service.list_active_domains()

    assert result[0]["options"][0]["value"] == 1
    assert service.get_active_domain("sexo_biologico") == result[0]


def test_domain_service_preserves_string_options() -> None:
    field = SimpleNamespace(
        name="historico_familiar",
        label="Historico",
        data_type="string",
        required=True,
        options=[SimpleNamespace(value="yes", label="Sim", display_order=1)],
    )
    service = DomainService(DomainRepositoryStub([field]))  # type: ignore[arg-type]

    assert service.list_active_domains()[0]["options"][0]["value"] == "yes"


def test_domain_service_raises_not_found() -> None:
    service = DomainService(DomainRepositoryStub([]))  # type: ignore[arg-type]
    with pytest.raises(DomainNotFoundError):
        service.get_active_domain("unknown")


def test_record_service_predicts_and_commits() -> None:
    record = SimpleNamespace(id=uuid4())
    repository = RecordRepositoryStub(record)
    transaction = TransactionStub()
    predictor = PredictorStub(
        {"probabilidade": 0.75, "faixa_risco": "alto", "acao_sugerida": "Intervenção imediata"}
    )
    service = DefasagemRiskRecordService(repository, transaction, predictor)  # type: ignore[arg-type]

    command = {"defasagem": 1.5, "idade": 10}
    assert service.create_record(command) is record
    assert repository.added == {
        "defasagem": 1.5,
        "idade": 10,
        "probabilidade": 0.75,
        "faixa_risco": "alto",
        "acao_sugerida": "Intervenção imediata",
    }
    assert predictor.called_with is command
    assert transaction.commits == 1
    assert transaction.rollbacks == 0


def test_record_service_rolls_back_on_repository_error() -> None:
    repository = RecordRepositoryStub(error=RuntimeError("database failed"))
    transaction = TransactionStub()
    predictor = PredictorStub()
    service = DefasagemRiskRecordService(repository, transaction, predictor)  # type: ignore[arg-type]

    with pytest.raises(RuntimeError, match="database failed"):
        service.create_record({"defasagem": 1.5, "idade": 10})
    assert transaction.commits == 0
    assert transaction.rollbacks == 1


def test_record_service_rolls_back_on_predictor_error() -> None:
    record = SimpleNamespace(id=uuid4())
    repository = RecordRepositoryStub(record)
    transaction = TransactionStub()
    predictor = PredictorStub(error=RuntimeError("model failed"))
    service = DefasagemRiskRecordService(repository, transaction, predictor)  # type: ignore[arg-type]

    with pytest.raises(RuntimeError, match="model failed"):
        service.create_record({"defasagem": 1.5, "idade": 10})
    assert repository.added is None
    assert transaction.commits == 0
    assert transaction.rollbacks == 1


def test_record_service_lists_all_records() -> None:
    records = [SimpleNamespace(id=index) for index in range(25)]
    service = DefasagemRiskRecordService(  # type: ignore[arg-type]
        RecordRepositoryStub(records=records), TransactionStub(), PredictorStub()
    )

    assert service.list_records() == records


def test_record_service_lists_empty_dataset() -> None:
    service = DefasagemRiskRecordService(  # type: ignore[arg-type]
        RecordRepositoryStub(records=[]), TransactionStub(), PredictorStub()
    )

    assert service.list_records() == []


def test_record_service_reads_or_raises_not_found() -> None:
    record = SimpleNamespace(id=uuid4())
    transaction = TransactionStub()
    predictor = PredictorStub()
    service = DefasagemRiskRecordService(  # type: ignore[arg-type]
        RecordRepositoryStub(record), transaction, predictor
    )
    assert service.get_record(record.id) is record

    missing = DefasagemRiskRecordService(  # type: ignore[arg-type]
        RecordRepositoryStub(), transaction, predictor
    )
    with pytest.raises(DefasagemRiskRecordNotFoundError):
        missing.get_record(uuid4())
