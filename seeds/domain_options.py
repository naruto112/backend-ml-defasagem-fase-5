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
        "label": "Defasagem escolar (fases, negativa = atrasado)",
        "type": "integer",
        "options": (),
        "min_value": -100,
        "max_value": 100,
    },
    {
        "name": "fase_ordem",
        "label": "Fase de escolaridade PEDE (ordem)",
        "type": "integer",
        "options": (
            ("0", "ALFA (1º e 2º ano)"),
            ("1", "Fase 1 (3º e 4º ano)"),
            ("2", "Fase 2 (5º e 6º ano)"),
            ("3", "Fase 3 (7º e 8º ano)"),
            ("4", "Fase 4 (9º ano)"),
            ("5", "Fase 5 (1º ano EM)"),
            ("6", "Fase 6 (2º ano EM)"),
            ("7", "Fase 7 (3º ano EM)"),
            ("8", "Fase 8 (Universitários)"),
        ),
    },
    {
        "name": "idade",
        "label": "Idade do aluno (anos)",
        "type": "integer",
        "options": (),
        "min_value": 1,
        "max_value": 99,
    },
    {
        "name": "ano_ingresso",
        "label": "Ano de ingresso na escola",
        "type": "integer",
        "options": (),
        "min_value": 2016,
        "max_value": 4000,
    },
    {
        "name": "ida",
        "label": "Indicador de Desempenho Acadêmico (IDA)",
        "type": "number",
        "options": (),
        "min_value": 0,
        "max_value": 100,
    },
    {
        "name": "ieg",
        "label": "Indicador de Engajamento (IEG)",
        "type": "number",
        "options": (),
        "min_value": 0,
        "max_value": 100,
    },
    {
        "name": "iaa",
        "label": "Indicador de Autoavaliação (IAA)",
        "type": "number",
        "options": (),
        "min_value": 0,
        "max_value": 100,
    },
    {
        "name": "ips",
        "label": "Indicador Psicossocial (IPS)",
        "type": "number",
        "options": (),
        "min_value": 0,
        "max_value": 100,
    },
    {
        "name": "ipv",
        "label": "Indicador de Ponto de Virada (IPV)",
        "type": "number",
        "options": (),
        "min_value": 0,
        "max_value": 100,
    },
    {
        "name": "inde",
        "label": "Índice de Desenvolvimento Educacional (INDE)",
        "type": "number",
        "options": (),
        "min_value": 0,
        "max_value": 100,
    },
    {
        "name": "genero",
        "label": "Gênero",
        "type": "string",
        "options": (("Feminino", "Feminino"), ("Masculino", "Masculino")),
    },
    {
        "name": "instituicao",
        "label": "Tipo de instituição",
        "type": "string",
        "options": (
            ("Pública", "Pública"),
            ("Privada", "Privada"),
            ("Privada - Programa de Apadrinhamento", "Privada - Programa de Apadrinhamento"),
            ("Privada *Parcerias com Bolsa 100%", "Privada *Parcerias com Bolsa 100%"),
            ("Privada - Pagamento por *Empresa Parceira", "Privada - Pagamento por *Empresa Parceira"),
            ("Concluiu o 3º EM", "Concluiu o 3º EM"),
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
                "min_value": field.get("min_value"),
                "max_value": field.get("max_value"),
            }
            field_insert = insert(DomainField.__table__).values(**field_values)
            field_id = connection.execute(
                field_insert.on_conflict_do_update(
                    constraint="uq_domain_field_name",
                    set_={
                        "label": field_values["label"],
                        "data_type": field_values["data_type"],
                        "display_order": field_values["display_order"],
                        "required": field_values["required"],
                        "active": field_values["active"],
                        "updated_at": func.now(),
                    },
                ).returning(DomainField.id)
            ).scalar_one()
            
            # Update min_value and max_value separately if they exist
            if field_values["min_value"] is not None or field_values["max_value"] is not None:
                update_values = {"updated_at": func.now()}
                if field_values["min_value"] is not None:
                    update_values["min_value"] = field_values["min_value"]
                if field_values["max_value"] is not None:
                    update_values["max_value"] = field_values["max_value"]
                connection.execute(
                    DomainField.__table__.update()
                    .where(DomainField.id == field_id)
                    .values(**update_values)
                )
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
