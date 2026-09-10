"""PEDE defasagem-risk form response model."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, Float, Index, SmallInteger, String, func
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db


class DefasagemRiskRecord(db.Model):  # type: ignore[name-defined]
    __tablename__ = "defasagem_risk_record"
    __table_args__ = (
        CheckConstraint("defasagem >= -4 AND defasagem <= 2", name="ck_defasagem_risk_defasagem"),
        CheckConstraint("fase_ordem BETWEEN 0 AND 8", name="ck_defasagem_risk_fase_ordem"),
        CheckConstraint("idade BETWEEN 7 AND 26", name="ck_defasagem_risk_idade"),
        CheckConstraint("ano_ingresso >= 2016 AND ano_ingresso <= 2023", name="ck_defasagem_risk_ano"),
        CheckConstraint("ida BETWEEN 0 AND 10", name="ck_defasagem_risk_ida"),
        CheckConstraint("ieg BETWEEN 0 AND 10", name="ck_defasagem_risk_ieg"),
        CheckConstraint("iaa BETWEEN 0 AND 10", name="ck_defasagem_risk_iaa"),
        CheckConstraint("ips BETWEEN 0 AND 10", name="ck_defasagem_risk_ips"),
        CheckConstraint("ipv BETWEEN 0 AND 10", name="ck_defasagem_risk_ipv"),
        CheckConstraint("inde BETWEEN 0 AND 10", name="ck_defasagem_risk_inde"),
        CheckConstraint(
            "genero IN ('Feminino', 'Masculino')",
            name="ck_defasagem_risk_genero",
        ),
        CheckConstraint(
            "instituicao IN ('Pública', 'Privada', 'Privada - Programa de Apadrinhamento', 'Privada *Parcerias com Bolsa 100%', 'Privada - Pagamento por *Empresa Parceira', 'Concluiu o 3º EM')",
            name="ck_defasagem_risk_instituicao",
        ),
        CheckConstraint(
            "probabilidade BETWEEN 0 AND 1",
            name="ck_defasagem_risk_probabilidade",
        ),
        CheckConstraint(
            "faixa_risco IN ('Baixo', 'M\u00e9dio', 'Alto')",
            name="ck_defasagem_risk_faixa",
        ),
        Index("ix_defasagem_risk_record_created_at", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4)
    defasagem: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    fase_ordem: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    idade: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    ano_ingresso: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    ida: Mapped[float] = mapped_column(Float, nullable=False)
    ieg: Mapped[float] = mapped_column(Float, nullable=False)
    iaa: Mapped[float] = mapped_column(Float, nullable=False)
    ips: Mapped[float] = mapped_column(Float, nullable=False)
    ipv: Mapped[float] = mapped_column(Float, nullable=False)
    inde: Mapped[float] = mapped_column(Float, nullable=False)
    genero: Mapped[str] = mapped_column(String(16), nullable=False)
    instituicao: Mapped[str] = mapped_column(String(64), nullable=False)
    probabilidade: Mapped[float] = mapped_column(Float, nullable=False)
    faixa_risco: Mapped[str] = mapped_column(String(16), nullable=False)
    acao_sugerida: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
