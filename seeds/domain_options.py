"""Upsert the canonical v1 domain catalog."""

# ruff: noqa: E501

from __future__ import annotations

import os
from typing import Any

from sqlalchemy import create_engine, func
from sqlalchemy.dialects.postgresql import insert

from app.models import DomainField, DomainOption

CATALOG: tuple[dict[str, Any], ...] = (
    {
        "name": "defasagem",
        "label": "Defasagem escolar (anos)",
        "type": "number",
        "options": (),
    },
    {
        "name": "fase_ordem",
        "label": "Fase de escolaridade (ordem)",
        "type": "integer",
        "options": (
            ("1", "1º ano"),
            ("2", "2º ano"),
            ("3", "3º ano"),
            ("4", "4º ano"),
            ("5", "5º ano"),
            ("6", "6º ano"),
            ("7", "7º ano"),
            ("8", "8º ano"),
            ("9", "9º ano"),
        ),
    },
    {
        "name": "idade",
        "label": "Idade do aluno (anos)",
        "type": "integer",
        "options": (),
    },
    {
        "name": "ano_ingresso",
        "label": "Ano de ingresso na escola",
        "type": "integer",
        "options": (),
    },
    {
        "name": "ida",
        "label": "Indicador de Desempenho Acadêmico (IDA)",
        "type": "number",
        "options": (),
    },
    {
        "name": "ieg",
        "label": "Indicador de Eficiência Escolar (IEG)",
        "type": "number",
        "options": (),
    },
    {
        "name": "iaa",
        "label": "Indicador de Aproveitamento Anual (IAA)",
        "type": "number",
        "options": (),
    },
    {
        "name": "ips",
        "label": "Indicador de Progresso Escolar (IPS)",
        "type": "number",
        "options": (),
    },
    {
        "name": "ipv",
        "label": "Indicador de Proficiência em Português (IPV)",
        "type": "number",
        "options": (),
    },
    {
        "name": "inde",
        "label": "Indicador de Desempenho Escolar (INDE)",
        "type": "number",
        "options": (),
    },
    {
        "name": "genero",
        "label": "Gênero",
        "type": "string",
        "options": (("masculino", "Masculino"), ("feminino", "Feminino")),
    },
    {
        "name": "instituicao",
        "label": "Tipo de instituição",
        "type": "string",
        "options": (("publica", "Pública"), ("privada", "Privada")),
    },
    {
        "name": "pedra",
        "label": "Pedra (classificação ordinal)",
        "type": "string",
        "options": (
            ("quartil_1", "Quartil 1"),
            ("quartil_2", "Quartil 2"),
            ("quartil_3", "Quartil 3"),
            ("quartil_4", "Quartil 4"),
        ),
    },
)


def seed(database_url: str) -> None:
    engine = create_engine(database_url)
    with engine.begin() as connection:
        for field_order, field in enumerate(CATALOG, start=1):
            field_values = {
                "name": field["name"],
                "label": field["label"],
                "data_type": field["type"],
                "display_order": field_order,
                "required": field.get("required", True),
                "active": True,
            }
            field_insert = insert(DomainField.__table__).values(**field_values)
            field_id = connection.execute(
                field_insert.on_conflict_do_update(
                    constraint="uq_domain_field_name",
                    set_={**field_values, "updated_at": func.now()},
                ).returning(DomainField.id)
            ).scalar_one()
            for option_order, (value, label) in enumerate(field["options"], start=1):
                option_values = {
                    "domain_field_id": field_id,
                    "value": value,
                    "label": label,
                    "display_order": option_order,
                    "active": True,
                }
                option_insert = insert(DomainOption.__table__).values(**option_values)
                connection.execute(
                    option_insert.on_conflict_do_update(
                        constraint="uq_domain_option_field_value",
                        set_={**option_values, "updated_at": func.now()},
                    )
                )
    engine.dispose()


def main() -> None:
    database_url = os.getenv("DATABASE_URL")
    if database_url is None or not database_url.strip():
        raise RuntimeError("DATABASE_URL is required")
    seed(database_url)


if __name__ == "__main__":
    main()
