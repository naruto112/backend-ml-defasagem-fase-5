"""PEDE defasagem-risk record HTTP routes."""

from typing import Any
from uuid import UUID

from flask import current_app, request, url_for
from flask.views import MethodView
from flask_smorest import Blueprint  # type: ignore[import-untyped]
from marshmallow import ValidationError

from app.api.errors import problem_response, validation_problem
from app.domain_catalog import RECORD_FIELDS
from app.extensions import db
from app.repositories import DefasagemRiskRecordRepository
from app.schemas import (
    DefasagemRiskRecordCreatedSchema,
    DefasagemRiskRecordListSchema,
    DefasagemRiskRecordReadSchema,
)
from app.schemas.defasagem_risk_record_schema import DefasagemRiskRecordCreateSchema
from app.services import DefasagemRiskRecordService

risk_record_blueprint = Blueprint(
    "defasagem-risk-records",
    "defasagem-risk-records",
    url_prefix="/api/v1/defasagem-risk-records",
    description="PEDE defasagem-risk records",
)


def _service() -> DefasagemRiskRecordService:
    predictor = current_app.config["ML_PREDICTOR"]
    return DefasagemRiskRecordService(
        DefasagemRiskRecordRepository(db.session), db.session, predictor
    )


def _isoformat(value: Any) -> str:
    return str(value.isoformat()).replace("+00:00", "Z")


def _serialize_record(record: Any) -> dict[str, Any]:
    result = {field: getattr(record, field) for field in RECORD_FIELDS}
    result.update({"id": record.id, "created_at": _isoformat(record.created_at)})
    return result


@risk_record_blueprint.route("")
class DefasagemRiskRecordCollection(MethodView):
    @risk_record_blueprint.doc(responses={"500": {"description": "Internal error"}})
    @risk_record_blueprint.response(200, DefasagemRiskRecordListSchema)
    def get(self) -> dict[str, Any]:
        records = _service().list_records()
        return {"data": [_serialize_record(record) for record in records]}

    @risk_record_blueprint.doc(
        requestBody={
            "required": True,
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/DefasagemRiskRecordCreate"}
                }
            },
        },
        responses={
            "400": {"description": "Empty or malformed JSON"},
            "413": {"description": "Body exceeds 64 KiB"},
            "415": {"description": "Content-Type is not JSON"},
            "422": {"description": "Payload validation failed"},
            "500": {"description": "Internal error"},
        },
    )
    @risk_record_blueprint.response(201, DefasagemRiskRecordCreatedSchema)
    def post(self) -> Any:
        if not request.is_json:
            return problem_response(
                415, "unsupported-media-type", "Midia nao suportada", "Use application/json."
            )
        if not request.get_data(cache=True):
            return problem_response(
                400, "invalid-json", "JSON invalido", "O corpo JSON esta vazio ou malformado."
            )
        payload = request.get_json()
        if not isinstance(payload, dict):
            return validation_problem({"$": ["invalid_type"]})
        try:
            command = DefasagemRiskRecordCreateSchema().load(payload)
        except ValidationError as error:
            messages = error.messages
            if not isinstance(messages, dict):
                messages = {"$": ["invalid_type"]}
            return validation_problem(messages)

        record = _service().create_record(command)
        location = url_for(
            "defasagem-risk-records.DefasagemRiskRecordItem",
            record_id=record.id,
        )
        return (
            {"id": record.id, "created_at": _isoformat(record.created_at)},
            201,
            {"Location": location},
        )


@risk_record_blueprint.route("/<string:record_id>")
class DefasagemRiskRecordItem(MethodView):
    @risk_record_blueprint.doc(
        responses={
            "400": {"description": "Malformed UUID"},
            "404": {"description": "Record not found"},
            "500": {"description": "Internal error"},
        }
    )
    @risk_record_blueprint.response(200, DefasagemRiskRecordReadSchema)
    def get(self, record_id: str) -> Any:
        try:
            parsed_id = UUID(record_id)
        except ValueError:
            return problem_response(
                400, "invalid-uuid", "UUID invalido", "O identificador nao e um UUID valido."
            )
        return _serialize_record(_service().get_record(parsed_id))
