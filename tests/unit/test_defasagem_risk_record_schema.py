from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest
from marshmallow import ValidationError

from app.domain_catalog import DOMAIN_VALUES, INPUT_FIELDS
from app.schemas import DefasagemRiskRecordCreateSchema


@pytest.fixture
def valid_payload() -> dict[str, Any]:
    return {
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
        "genero": "masculino",
        "instituicao": "publica",
        "pedra": "quartil_1",
    }


INPUT_DOMAIN_VALUES = {k: v for k, v in DOMAIN_VALUES.items() if k != "obesity"}


def _assert_error(payload: dict[str, Any], field: str, code: str) -> None:
    with pytest.raises(ValidationError) as raised:
        DefasagemRiskRecordCreateSchema().load(payload)
    assert code in raised.value.messages[field]


def test_valid_payload_round_trips(valid_payload: dict[str, Any]) -> None:
    assert DefasagemRiskRecordCreateSchema().load(valid_payload) == valid_payload
    assert tuple(valid_payload) == INPUT_FIELDS


@pytest.mark.parametrize("idade", [6, 10, 15, 18])
def test_ct_idade_01_accepts_boundaries(valid_payload: dict[str, Any], idade: int) -> None:
    valid_payload["idade"] = idade
    assert DefasagemRiskRecordCreateSchema().load(valid_payload)["idade"] == idade


@pytest.mark.parametrize("idade", [0, -1, 19, 150, 2147483647])
def test_ct_idade_02_03_rejects_out_of_range(valid_payload: dict[str, Any], idade: int) -> None:
    valid_payload["idade"] = idade
    _assert_error(valid_payload, "idade", "out_of_range")


@pytest.mark.parametrize("value", [35.5, "35", True, {}, []])
def test_ct_idade_04_rejects_non_integer_types(valid_payload: dict[str, Any], value: Any) -> None:
    valid_payload["idade"] = value
    _assert_error(valid_payload, "idade", "invalid_type")


@pytest.mark.parametrize("field", INPUT_FIELDS)
def test_null_is_rejected(valid_payload: dict[str, Any], field: str) -> None:
    valid_payload[field] = None
    _assert_error(valid_payload, field, "null_not_allowed")


@pytest.mark.parametrize("field", INPUT_FIELDS)
def test_omitted_field_is_rejected(valid_payload: dict[str, Any], field: str) -> None:
    valid_payload.pop(field)
    _assert_error(valid_payload, field, "required")


@pytest.mark.parametrize(
    ("field", "values"),
    [(field, values) for field, values in INPUT_DOMAIN_VALUES.items()],
)
def test_each_domain_value_is_accepted(
    valid_payload: dict[str, Any], field: str, values: tuple[Any, ...]
) -> None:
    for value in values:
        payload = deepcopy(valid_payload)
        payload[field] = value
        assert ObesityRecordCreateSchema().load(payload)[field] == value


@pytest.mark.parametrize("field", INPUT_DOMAIN_VALUES)
def test_value_outside_domain_is_rejected(valid_payload: dict[str, Any], field: str) -> None:
    valid_payload[field] = 999 if isinstance(INPUT_DOMAIN_VALUES[field][0], int) else "invalid"
    _assert_error(valid_payload, field, "invalid_domain")


@pytest.mark.parametrize("field", INPUT_DOMAIN_VALUES)
def test_domain_field_rejects_wrong_type(valid_payload: dict[str, Any], field: str) -> None:
    valid_payload[field] = (
        str(INPUT_DOMAIN_VALUES[field][0]) if isinstance(INPUT_DOMAIN_VALUES[field][0], int) else 1
    )
    _assert_error(valid_payload, field, "invalid_type")


def test_unknown_field_is_rejected(valid_payload: dict[str, Any]) -> None:
    valid_payload["extra"] = "value"
    _assert_error(valid_payload, "extra", "unknown_field")


def test_risco_defasagem_in_payload_is_rejected(valid_payload: dict[str, Any]) -> None:
    valid_payload["risco_defasagem"] = "alto"
    _assert_error(valid_payload, "risco_defasagem", "unknown_field")
