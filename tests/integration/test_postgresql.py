from __future__ import annotations

import os
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain_catalog import INPUT_FIELDS
from app.models import DefasagemRiskRecord, DomainField, DomainOption
from app.repositories import DefasagemRiskRecordRepository, DomainRepository
from seeds.domain_options import seed

DATABASE_URL = os.getenv("DATABASE_URL", "")
pytestmark = pytest.mark.skipif(
    os.getenv("RUN_POSTGRES_TESTS") != "1",
    reason="set RUN_POSTGRES_TESTS=1 with a disposable PostgreSQL database",
)


def test_ct_db_seed_is_idempotent_and_catalog_is_complete() -> None:
    seed(DATABASE_URL)
    seed(DATABASE_URL)
    engine = create_engine(DATABASE_URL)
    with Session(engine) as session:
        assert session.scalar(select(func.count()).select_from(DomainField)) == 13
        assert session.scalar(select(func.count()).select_from(DomainOption)) == 17
        domains = DomainRepository(session).list_active_with_options()
        assert len(domains) == 13
        assert [domain.name for domain in domains] == list(INPUT_FIELDS)
        by_name = {domain.name: domain for domain in domains}
        assert [option.value for option in by_name["genero"].options] == ["Feminino", "Masculino"]
        assert [option.value for option in by_name["instituicao"].options] == ["Pública", "Privada"]
    engine.dispose()


def test_ct_db_record_round_trip_and_check_constraint() -> None:
    engine = create_engine(DATABASE_URL)
    valid = {
        "defasagem": 1.5,
        "fase_ordem": 3,
        "idade": 10,
        "ano_ingresso": 2020,
        "ida": 7.8,
        "ieg": 8.2,
        "iaa": 6.5,
        "ips": 9.1,
        "ipv": 7.3,
        "inde": 8.0,
        "genero": "Feminino",
        "instituicao": "Pública",
        "pedra": "Quartzo",
        "probabilidade": 0.75,
        "faixa_risco": "Alto",
        "acao_sugerida": "Prioridade de acompanhamento",
    }
    with Session(engine, expire_on_commit=False) as session:
        repository = DefasagemRiskRecordRepository(session)
        record = repository.add(valid)
        session.commit()
        assert repository.get_by_id(record.id).idade == 10  # type: ignore[union-attr]

        invalid = DefasagemRiskRecord(id=uuid4(), **{**valid, "idade": 19})
        session.add(invalid)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
    engine.dispose()
