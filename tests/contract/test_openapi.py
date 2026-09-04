from __future__ import annotations

import pytest

from app import create_app


@pytest.fixture
def app(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://test:test@invalid/test")
    return create_app()


def test_ct_contrato_openapi_contains_all_routes_and_input_schema(app) -> None:
    document = app.test_client().get("/api/openapi.json").get_json()
    assert set(document["paths"]) == {
        "/health/live",
        "/health/ready",
        "/api/v1/domains",
        "/api/v1/domains/{field_name}",
        "/api/v1/defasagem-risk-records",
        "/api/v1/defasagem-risk-records/{record_id}",
    }
    create = document["components"]["schemas"]["DefasagemRiskRecordCreate"]
    assert len(create["required"]) == 13
    assert "probabilidade" not in create["required"]
    assert "faixa_risco" not in create["required"]
    assert "acao_sugerida" not in create["required"]
    post = document["paths"]["/api/v1/defasagem-risk-records"]["post"]
    assert post["requestBody"]["required"] is True
    assert {"201", "400", "413", "415", "422", "500"}.issubset(post["responses"])
