"""Database models exposed for Alembic metadata discovery."""

from app.models.domain import DomainField, DomainOption
from app.models.defasagem_risk_record import DefasagemRiskRecord

__all__ = ["DefasagemRiskRecord", "DomainField", "DomainOption"]
