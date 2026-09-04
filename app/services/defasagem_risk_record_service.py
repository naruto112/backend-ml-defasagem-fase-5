"""PEDE defasagem-risk record use cases and transaction boundary."""

from collections.abc import Mapping
from typing import Any, Protocol
from uuid import UUID

from app.repositories import DefasagemRiskRecordRepository


class Transaction(Protocol):
    def commit(self) -> None: ...

    def rollback(self) -> None: ...


class DefasagemRiskPredictor(Protocol):
    def predict(self, command: Mapping[str, Any]) -> Mapping[str, Any]: ...


class DefasagemRiskRecordNotFoundError(LookupError):
    pass


class DefasagemRiskRecordService:
    def __init__(
        self,
        repository: DefasagemRiskRecordRepository,
        transaction: Transaction,
        predictor: DefasagemRiskPredictor,
    ) -> None:
        self._repository = repository
        self._transaction = transaction
        self._predictor = predictor

    def create_record(self, command: Mapping[str, Any]) -> Any:
        try:
            prediction = dict(self._predictor.predict(command))
            full_record = {**command, **prediction}
            record = self._repository.add(full_record)
            self._transaction.commit()
            return record
        except Exception:
            self._transaction.rollback()
            raise

    def get_record(self, record_id: UUID) -> Any:
        record = self._repository.get_by_id(record_id)
        if record is None:
            raise DefasagemRiskRecordNotFoundError(str(record_id))
        return record

    def list_records(self) -> list[Any]:
        return list(self._repository.list_all())
