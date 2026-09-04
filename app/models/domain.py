"""Domain catalog persistence models."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    SmallInteger,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db


class DomainField(db.Model):  # type: ignore[name-defined]
    __tablename__ = "domain_field"
    __table_args__ = (
        UniqueConstraint("name", name="uq_domain_field_name"),
        CheckConstraint(
            "data_type IN ('integer', 'number', 'string')",
            name="ck_domain_field_data_type",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    label: Mapped[str] = mapped_column(String(128), nullable=False)
    data_type: Mapped[str] = mapped_column(String(16), nullable=False)
    display_order: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    options: Mapped[list[DomainOption]] = relationship(
        back_populates="field",
        cascade="all, delete-orphan",
        order_by="DomainOption.display_order",
    )


class DomainOption(db.Model):  # type: ignore[name-defined]
    __tablename__ = "domain_option"
    __table_args__ = (
        UniqueConstraint("domain_field_id", "value", name="uq_domain_option_field_value"),
        Index(
            "ix_domain_option_field_active_order",
            "domain_field_id",
            "active",
            "display_order",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    domain_field_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("domain_field.id", name="fk_domain_option_domain_field"),
        nullable=False,
    )
    value: Mapped[str] = mapped_column(String(64), nullable=False)
    label: Mapped[str] = mapped_column(String(128), nullable=False)
    display_order: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    field: Mapped[DomainField] = relationship(back_populates="options")
