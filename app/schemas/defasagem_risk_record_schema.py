"""Schemas for PEDE defasagem-risk commands."""

from marshmallow import RAISE, Schema, fields, validate

from app.domain_catalog import DOMAIN_VALUES, RISK_BANDS
from app.schemas.fields import StrictInteger, StrictNumber, StrictString

COMMON_ERRORS = {
    "required": "required",
    "null": "null_not_allowed",
}


def _score_field() -> StrictNumber:
    return StrictNumber(
        required=True,
        allow_none=False,
        validate=validate.Range(min=0, max=10, error="out_of_range"),
        error_messages=COMMON_ERRORS,
    )


def _string_domain(field_name: str) -> StrictString:
    return StrictString(
        required=True,
        allow_none=False,
        validate=validate.OneOf(DOMAIN_VALUES[field_name], error="invalid_domain"),
        error_messages=COMMON_ERRORS,
    )


class DefasagemRiskRecordCreateSchema(Schema):
    """Validate the exact 12-field PEDE risk input contract."""

    error_messages = {"unknown": "unknown_field"}

    class Meta:
        unknown = RAISE

    defasagem = StrictInteger(
        required=True,
        allow_none=False,
        validate=validate.Range(min=-4, max=2, error="out_of_range"),
        error_messages=COMMON_ERRORS,
    )
    fase_ordem = StrictInteger(
        required=True,
        allow_none=False,
        validate=validate.Range(min=0, max=8, error="out_of_range"),
        error_messages=COMMON_ERRORS,
    )
    idade = StrictInteger(
        required=True,
        allow_none=False,
        validate=validate.Range(min=7, max=26, error="out_of_range"),
        error_messages=COMMON_ERRORS,
    )
    ano_ingresso = StrictInteger(
        required=True,
        allow_none=False,
        validate=validate.Range(min=2016, max=2023, error="out_of_range"),
        error_messages=COMMON_ERRORS,
    )
    ida = _score_field()
    ieg = _score_field()
    iaa = _score_field()
    ips = _score_field()
    ipv = _score_field()
    inde = _score_field()
    genero = _string_domain("genero")
    instituicao = _string_domain("instituicao")


class DefasagemRiskRecordCreatedSchema(Schema):
    id = fields.UUID(required=True)
    created_at = fields.String(required=True)


class DefasagemRiskRecordReadSchema(Schema):
    """Read schema with 12 inputs plus server-derived risk fields."""

    id = fields.UUID(required=True)
    created_at = fields.String(required=True)

    defasagem = StrictInteger(required=True)
    fase_ordem = StrictInteger(required=True)
    idade = StrictInteger(required=True)
    ano_ingresso = StrictInteger(required=True)
    ida = StrictNumber(required=True)
    ieg = StrictNumber(required=True)
    iaa = StrictNumber(required=True)
    ips = StrictNumber(required=True)
    ipv = StrictNumber(required=True)
    inde = StrictNumber(required=True)
    genero = StrictString(required=True)
    instituicao = StrictString(required=True)
    probabilidade = StrictNumber(
        required=True,
        validate=validate.Range(min=0, max=1, error="out_of_range"),
    )
    faixa_risco = StrictString(
        required=True,
        validate=validate.OneOf(RISK_BANDS, error="invalid_domain"),
    )
    acao_sugerida = StrictString(required=True)


class DefasagemRiskRecordListSchema(Schema):
    """Collection of all PEDE defasagem-risk records."""

    data = fields.List(fields.Nested(DefasagemRiskRecordReadSchema), required=True)


__all__ = [
    "DefasagemRiskRecordCreateSchema",
    "DefasagemRiskRecordCreatedSchema",
    "DefasagemRiskRecordListSchema",
    "DefasagemRiskRecordReadSchema",
]
