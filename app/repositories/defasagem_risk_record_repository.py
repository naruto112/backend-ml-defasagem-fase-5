"""Persistence operations for PEDE defasagem-risk records."""

from collections.abc import Mapping
from typing import Any, cast
from uuid import UUID

from sqlalchemy import select

from app.models import DefasagemRiskRecord


class DefasagemRiskRecordRepository:
    def __init__(self, session: Any) -> None:
        self._session = session

    def add(self, values: Mapping[str, Any]) -> DefasagemRiskRecord:
        record = DefasagemRiskRecord(**values)
        self._session.add(record)
        self._session.flush()
        return record

    def get_by_id(self, record_id: UUID) -> DefasagemRiskRecord | None:
        return cast(DefasagemRiskRecord | None, self._session.get(DefasagemRiskRecord, record_id))

    def list_all(self) -> list[DefasagemRiskRecord]:
        statement = select(DefasagemRiskRecord).order_by(
            DefasagemRiskRecord.created_at.desc(), DefasagemRiskRecord.id.desc()
        )
        return list(self._session.scalars(statement))
