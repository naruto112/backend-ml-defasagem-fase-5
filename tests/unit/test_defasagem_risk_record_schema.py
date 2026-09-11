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
        "defasagem": -1,
        "fase_ordem": 2,
        "idade": 12,
        "ano_ingresso": 2022,
        "ida": 7.8,
        "ieg": 8.2,
        "iaa": 6.5,
        "ips": 9.1,
        "ipv": 7.3,
        "inde": 8.0,
        "genero": "Feminino",
        "instituicao": "Pública",
    }


INPUT_DOMAIN_VALUES = {k: v for k, v in DOMAIN_VALUES.items() if k in INPUT_FIELDS}


def _assert_error(payload: dict[str, Any], field: str, code: str) -> None:
    with pytest.raises(ValidationError) as raised:
        DefasagemRiskRecordCreateSchema().load(payload)
    assert code in raised.value.messages[field]


def test_valid_payload_round_trips(valid_payload: dict[str, Any]) -> None:
    assert DefasagemRiskRecordCreateSchema().load(valid_payload) == valid_payload
    assert tuple(valid_payload) == INPUT_FIELDS


@pytest.mark.parametrize("idade", [1, 12, 50, 99])
def test_ct_idade_01_accepts_boundaries(valid_payload: dict[str, Any], idade: int) -> None:
    valid_payload["idade"] = idade
    assert DefasagemRiskRecordCreateSchema().load(valid_payload)["idade"] == idade


@pytest.mark.parametrize("idade", [0, 100, 150, 2147483647])
def test_ct_idade_02_03_rejects_out_of_range(valid_payload: dict[str, Any], idade: int) -> None:
    valid_payload["idade"] = idade
    _assert_error(valid_payload, "idade", "out_of_range")


@pytest.mark.parametrize("value", [35.5, "35", True, {}, []])
def test_ct_idade_04_rejects_non_integer_types(valid_payload: dict[str, Any], value: Any) -> None:
    valid_payload["idade"] = value
    _assert_error(valid_payload, "idade", "invalid_type")


@pytest.mark.parametrize("defasagem", [-100, -50, -1, 0, 50, 100])
def test_ct_defasagem_accepts_boundaries(valid_payload: dict[str, Any], defasagem: int) -> None:
    valid_payload["defasagem"] = defasagem
    assert DefasagemRiskRecordCreateSchema().load(valid_payload)["defasagem"] == defasagem


@pytest.mark.parametrize("defasagem", [-101, 101, 200])
def test_ct_defasagem_rejects_out_of_range(valid_payload: dict[str, Any], defasagem: int) -> None:
    valid_payload["defasagem"] = defasagem
    _assert_error(valid_payload, "defasagem", "out_of_range")


@pytest.mark.parametrize("defasagem", [1.5, True, {}, []])
def test_ct_defasagem_rejects_wrong_type(valid_payload: dict[str, Any], defasagem: Any) -> None:
    valid_payload["defasagem"] = defasagem
    _assert_error(valid_payload, "defasagem", "invalid_type")


@pytest.mark.parametrize("ano_ingresso", [2016, 2020, 2023, 3000, 4000])
def test_ct_ano_ingresso_accepts_boundaries(valid_payload: dict[str, Any], ano_ingresso: int) -> None:
    valid_payload["ano_ingresso"] = ano_ingresso
    assert DefasagemRiskRecordCreateSchema().load(valid_payload)["ano_ingresso"] == ano_ingresso


@pytest.mark.parametrize("ano_ingresso", [2015, 4001, 5000, 2147483647])
def test_ct_ano_ingresso_rejects_out_of_range(valid_payload: dict[str, Any], ano_ingresso: int) -> None:
    valid_payload["ano_ingresso"] = ano_ingresso
    _assert_error(valid_payload, "ano_ingresso", "out_of_range")


@pytest.mark.parametrize("score_field", ["ida", "ieg", "iaa", "ips", "ipv", "inde"])
@pytest.mark.parametrize("score_value", [0, 5.5, 10, 50, 100])
def test_ct_score_fields_accept_new_boundaries(valid_payload: dict[str, Any], score_field: str, score_value: float) -> None:
    valid_payload[score_field] = score_value
    assert DefasagemRiskRecordCreateSchema().load(valid_payload)[score_field] == score_value


@pytest.mark.parametrize("score_field", ["ida", "ieg", "iaa", "ips", "ipv", "inde"])
@pytest.mark.parametrize("score_value", [-1, 101, 150])
def test_ct_score_fields_reject_out_of_range(valid_payload: dict[str, Any], score_field: str, score_value: float) -> None:
    valid_payload[score_field] = score_value
    _assert_error(valid_payload, score_field, "out_of_range")


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
        assert DefasagemRiskRecordCreateSchema().load(payload)[field] == value


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
