from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
from flask import Flask

from app import create_app
from app.api import domain_routes, defasagem_risk_record_routes
from app.domain_catalog import RECORD_FIELDS
from app.services import DomainNotFoundError, DefasagemRiskRecordNotFoundError

VALID_INPUT = {
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
    "genero": "Feminino",
    "instituicao": "Pública",
    "pedra": "Quartzo",
}


@pytest.fixture
def app(monkeypatch: pytest.MonkeyPatch) -> Flask:
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://test:test@invalid/test")
    return create_app()


@pytest.fixture
def valid_payload() -> dict[str, object]:
    return {**VALID_INPUT}


class DomainServiceStub:
    def list_active_domains(self):
        return [
            {
                "field": "sexo_biologico",
                "label": "Sexo biologico",
                "type": "integer",
                "required": True,
                "options": [{"value": 1, "label": "Masculino", "order": 1}],
            },
            {
                "field": "monitora_calorias",
                "label": "Monitora calorias consumidas",
                "type": "string",
                "required": True,
                "options": [
                    {"value": "yes", "label": "Sim", "order": 1},
                    {"value": "no", "label": "Nao", "order": 2},
                ],
            },
            {
                "field": "fuma",
                "label": "Fumante",
                "type": "string",
                "required": True,
                "options": [
                    {"value": "yes", "label": "Sim", "order": 1},
                    {"value": "no", "label": "Nao", "order": 2},
                ],
            },
        ]

    def get_active_domain(self, field_name: str):
        if field_name == "unknown":
            raise DomainNotFoundError(field_name)
        return self.list_active_domains()[0]


class RecordServiceStub:
    def __init__(self, payload):
        record_data = {
            **payload,
            "probabilidade": 0.75,
            "faixa_risco": "alto",
            "acao_sugerida": "Intervenção imediata",
        }
        self.record = SimpleNamespace(
            id=uuid4(), created_at=datetime(2026, 7, 3, tzinfo=timezone.utc), **record_data
        )

    def create_record(self, command):
        return self.record

    def get_record(self, record_id):
        if record_id != self.record.id:
            raise DefasagemRiskRecordNotFoundError(str(record_id))
        return self.record

    def list_records(self):
        return [self.record]


def test_liveness_openapi_and_request_id(app: Flask) -> None:
    client = app.test_client()

    live = client.get("/health/live", headers={"X-Request-ID": "request-123"})
    openapi = client.get("/api/openapi.json")

    assert live.status_code == 200
    assert live.headers["X-Request-ID"] == "request-123"
    assert openapi.status_code == 200
    assert "/api/v1/defasagem-risk-records" in openapi.get_json()["paths"]


def test_invalid_request_id_is_replaced(app: Flask) -> None:
    response = app.test_client().get("/health/live", headers={"X-Request-ID": "bad id"})
    assert response.headers["X-Request-ID"] != "bad id"
    assert len(response.headers["X-Request-ID"]) == 36


def test_domain_routes_and_not_found(app: Flask, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(domain_routes, "_service", DomainServiceStub)
    client = app.test_client()

    listed = client.get("/api/v1/domains")
    item = client.get("/api/v1/domains/sexo_biologico")
    missing = client.get("/api/v1/domains/unknown")

    assert listed.status_code == 200
    assert listed.get_json()["data"][0]["options"][0]["value"] == 1
    domains = {domain["field"]: domain for domain in listed.get_json()["data"]}
    assert [option["value"] for option in domains["monitora_calorias"]["options"]] == ["yes", "no"]
    assert [option["value"] for option in domains["fuma"]["options"]] == ["yes", "no"]
    assert item.status_code == 200
    assert missing.status_code == 404
    assert missing.content_type == "application/problem+json"


def test_record_post_get_and_location(
    app: Flask,
    valid_payload: dict[str, object],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = RecordServiceStub(valid_payload)
    monkeypatch.setattr(defasagem_risk_record_routes, "_service", lambda: service)
    client = app.test_client()

    created = client.post("/api/v1/defasagem-risk-records", json=valid_payload)
    fetched = client.get(created.headers["Location"])

    assert created.status_code == 201
    assert created.get_json()["id"] == str(service.record.id)
    assert fetched.status_code == 200
    assert fetched.get_json()["idade"] == 10
    assert set(RECORD_FIELDS).issubset(fetched.get_json())


def test_record_list_returns_all(
    app: Flask,
    valid_payload: dict[str, object],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = RecordServiceStub(valid_payload)
    monkeypatch.setattr(defasagem_risk_record_routes, "_service", lambda: service)

    response = app.test_client().get("/api/v1/defasagem-risk-records")

    assert response.status_code == 200
    body = response.get_json()
    assert len(body["data"]) == 1
    assert set(RECORD_FIELDS).issubset(body["data"][0])


@pytest.mark.parametrize(
    ("kwargs", "status"),
    [
        ({"data": "{}"}, 415),
        ({"data": "", "content_type": "application/json"}, 400),
        ({"data": "{", "content_type": "application/json"}, 400),
        ({"json": []}, 422),
        ({"json": {"idade": 35}}, 422),
    ],
)
def test_record_post_rejects_invalid_requests(
    app: Flask, kwargs: dict[str, object], status: int
) -> None:
    response = app.test_client().post("/api/v1/defasagem-risk-records", **kwargs)
    assert response.status_code == status
    assert response.content_type == "application/problem+json"


def test_record_get_rejects_invalid_and_missing_uuid(
    app: Flask,
    valid_payload: dict[str, object],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = RecordServiceStub(valid_payload)
    monkeypatch.setattr(defasagem_risk_record_routes, "_service", lambda: service)
    client = app.test_client()

    invalid = client.get("/api/v1/defasagem-risk-records/not-a-uuid")
    missing = client.get(f"/api/v1/defasagem-risk-records/{uuid4()}")

    assert invalid.status_code == 400
    assert missing.status_code == 404
