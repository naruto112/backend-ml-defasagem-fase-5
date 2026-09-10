"""Canonical PEDE defasagem-risk field names and accepted domain values."""

from __future__ import annotations

from types import MappingProxyType
from typing import Final, Literal

DomainType = Literal["integer", "number", "string"]

INPUT_FIELDS: Final[tuple[str, ...]] = (
    "defasagem",
    "fase_ordem",
    "idade",
    "ano_ingresso",
    "ida",
    "ieg",
    "iaa",
    "ips",
    "ipv",
    "inde",
    "genero",
    "instituicao",
)

DERIVED_FIELDS: Final[tuple[str, ...]] = (
    "probabilidade",
    "faixa_risco",
    "acao_sugerida",
)

RECORD_FIELDS: Final[tuple[str, ...]] = INPUT_FIELDS + DERIVED_FIELDS

RISK_BANDS: Final[tuple[str, ...]] = ("Baixo", "M\u00e9dio", "Alto")

DOMAIN_VALUES = MappingProxyType(
    {
        "genero": ("Feminino", "Masculino"),
        "instituicao": (
            "Pública",
            "Privada",
            "Privada - Programa de Apadrinhamento",
            "Privada *Parcerias com Bolsa 100%",
            "Privada - Pagamento por *Empresa Parceira",
            "Concluiu o 3º EM",
        ),
        "faixa_risco": RISK_BANDS,
    }
)


__all__ = [
    "DERIVED_FIELDS",
    "DOMAIN_VALUES",
    "DomainType",
    "INPUT_FIELDS",
    "RECORD_FIELDS",
    "RISK_BANDS",
]
