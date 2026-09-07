"""Tests for app.ml package (feature_transformer, model_loader, predictor)."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import joblib
import numpy as np
import pandas as pd
import pytest

from app.ml.feature_transformer import FEATURE_COLUMNS, FeatureTransformer
from app.ml.model_loader import ModelArtifactError, _sha256, load_model, verify_artifact
from app.ml.predictor import DEFAULT_RISK_BANDS, DefasagemRiskPredictor, PredictionError

SAMPLE_COMMAND = {
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


class _FakeModel:
    def __init__(self, proba_return_value=None) -> None:
        self.proba_return_value = (
            np.array([[0.5, 0.5]]) if proba_return_value is None else proba_return_value
        )
        self.seen: pd.DataFrame | None = None

    def predict_proba(self, X):
        self.seen = X
        return self.proba_return_value


def _make_artifact(proba_return_value=None, model=None) -> dict[str, object]:
    return {
        "modelo": model or _FakeModel(proba_return_value),
        "features": list(FEATURE_COLUMNS),
        "faixas_risco": list(DEFAULT_RISK_BANDS),
    }


def _write_artifact(
    tmp_path: Path, artifact: object, **manifest_extra: object
) -> tuple[Path, Path]:
    model_file = tmp_path / "model.joblib"
    joblib.dump(artifact, model_file)
    manifest_file = tmp_path / "manifest.json"
    manifest_file.write_text(
        json.dumps(
            {
                "sha256": _sha256(model_file),
                "size_bytes": model_file.stat().st_size,
                **manifest_extra,
            }
        )
    )
    return model_file, manifest_file


class TestFeatureTransformer:
    def test_output_shape_and_columns(self):
        transformer = FeatureTransformer()
        df = transformer.transform(SAMPLE_COMMAND)
        assert isinstance(df, pd.DataFrame)
        assert list(df.columns) == FEATURE_COLUMNS
        assert len(df) == 1

    def test_categorical_values_are_kept_raw(self):
        transformer = FeatureTransformer()
        cmd = {**SAMPLE_COMMAND, "genero": "Masculino", "instituicao": "Privada", "pedra": "Ágata"}
        row = transformer.transform(cmd).iloc[0]
        assert row["genero"] == "Masculino"
        assert row["instituicao"] == "Privada"
        assert row["pedra"] == "Ágata"

    def test_numeric_values_are_cast(self):
        transformer = FeatureTransformer()
        cmd = {**SAMPLE_COMMAND, "defasagem": 2, "idade": 11.0}
        row = transformer.transform(cmd).iloc[0]
        assert row["defasagem"] == 2.0
        assert row["idade"] == 11


class TestModelLoader:
    def test_verify_artifact_missing_manifest(self, tmp_path: Path):
        model_file = tmp_path / "model.joblib"
        model_file.write_bytes(b"fake")
        with pytest.raises(ModelArtifactError, match="Manifest not found"):
            verify_artifact(model_file, tmp_path / "missing.json")

    def test_verify_artifact_missing_model(self, tmp_path: Path):
        manifest_file = tmp_path / "manifest.json"
        manifest_file.write_text(json.dumps({"sha256": "abc", "size_bytes": 4}))
        with pytest.raises(ModelArtifactError, match="Model file not found"):
            verify_artifact(tmp_path / "missing.joblib", manifest_file)

    def test_verify_artifact_sha_mismatch(self, tmp_path: Path):
        model_file = tmp_path / "model.joblib"
        model_file.write_bytes(b"fake model data")
        manifest_file = tmp_path / "manifest.json"
        manifest_file.write_text(
            json.dumps({"sha256": "0000000000000000", "size_bytes": model_file.stat().st_size})
        )
        with pytest.raises(ModelArtifactError, match="SHA-256 mismatch"):
            verify_artifact(model_file, manifest_file)

    def test_verify_artifact_size_mismatch(self, tmp_path: Path):
        model_file = tmp_path / "model.joblib"
        model_file.write_bytes(b"fake model data")
        real_sha = _sha256(model_file)
        manifest_file = tmp_path / "manifest.json"
        manifest_file.write_text(json.dumps({"sha256": real_sha, "size_bytes": 9999}))
        with pytest.raises(ModelArtifactError, match="Size mismatch"):
            verify_artifact(model_file, manifest_file)

    def test_verify_artifact_success(self, tmp_path: Path):
        model_file = tmp_path / "model.joblib"
        model_file.write_bytes(b"fake model data")
        real_sha = _sha256(model_file)
        manifest_file = tmp_path / "manifest.json"
        manifest_file.write_text(
            json.dumps({"sha256": real_sha, "size_bytes": model_file.stat().st_size})
        )
        result = verify_artifact(model_file, manifest_file)
        assert result["sha256"] == real_sha

    def test_load_model_rejects_non_mapping_artifact(self, tmp_path: Path):
        model_file, manifest_file = _write_artifact(tmp_path, SimpleNamespace())
        with pytest.raises(ModelArtifactError, match="must be a mapping"):
            load_model(model_file, manifest_file)

    def test_load_model_rejects_missing_keys(self, tmp_path: Path):
        model_file, manifest_file = _write_artifact(tmp_path, {"modelo": _FakeModel()})
        with pytest.raises(
            ModelArtifactError, match="missing required keys: faixas_risco, features"
        ):
            load_model(model_file, manifest_file)

    def test_load_model_type_mismatch(self, tmp_path: Path):
        model_file, manifest_file = _write_artifact(
            tmp_path, _make_artifact(), algorithm="HistGradientBoostingClassifier"
        )
        with pytest.raises(ModelArtifactError, match="Model type mismatch"):
            load_model(model_file, manifest_file)

    def test_load_model_feature_mismatch(self, tmp_path: Path):
        model_file, manifest_file = _write_artifact(tmp_path, _make_artifact(), features=["idade"])
        with pytest.raises(ModelArtifactError, match="Feature mismatch"):
            load_model(model_file, manifest_file)

    def test_load_model_success(self, tmp_path: Path):
        model_file, manifest_file = _write_artifact(
            tmp_path, _make_artifact(), algorithm="_FakeModel", features=FEATURE_COLUMNS
        )
        result = load_model(model_file, manifest_file)
        assert list(result["features"]) == FEATURE_COLUMNS


class TestDefasagemRiskPredictor:
    def test_predict_returns_dict_with_probability_and_action(self):
        predictor = DefasagemRiskPredictor(_make_artifact(np.array([[0.3, 0.7]])))
        result = predictor.predict(SAMPLE_COMMAND)
        assert result["probabilidade"] == pytest.approx(0.7)
        assert result["faixa_risco"] == "Alto"
        assert result["acao_sugerida"] == "Prioridade de acompanhamento"

    def test_predict_medium_band(self):
        predictor = DefasagemRiskPredictor(_make_artifact(np.array([[0.7, 0.3]])))
        assert predictor.predict(SAMPLE_COMMAND)["faixa_risco"] == "Médio"

    def test_predict_low_band(self):
        predictor = DefasagemRiskPredictor(_make_artifact(np.array([[0.9, 0.1]])))
        result = predictor.predict(SAMPLE_COMMAND)
        assert result["probabilidade"] == pytest.approx(0.1)
        assert result["faixa_risco"] == "Baixo"

    def test_predict_uses_artifact_risk_bands(self):
        artifact = _make_artifact(np.array([[0.4, 0.6]]))
        artifact["faixas_risco"] = [("Custom", 0.0, 1.01, "Agir")]
        result = DefasagemRiskPredictor(artifact).predict(SAMPLE_COMMAND)
        assert result["faixa_risco"] == "Custom"
        assert result["acao_sugerida"] == "Agir"

    def test_predict_selects_artifact_feature_columns(self):
        model = _FakeModel()
        artifact = _make_artifact(model=model)
        artifact["features"] = ["idade", "inde"]
        DefasagemRiskPredictor(artifact).predict(SAMPLE_COMMAND)
        assert model.seen is not None
        assert list(model.seen.columns) == ["idade", "inde"]

    def test_predict_unexpected_shape_raises(self):
        predictor = DefasagemRiskPredictor(_make_artifact(np.array([[0.5, 0.5], [0.5, 0.5]])))
        with pytest.raises(PredictionError, match="unexpected probability shape"):
            predictor.predict(SAMPLE_COMMAND)

    def test_predict_invalid_probability_raises(self):
        predictor = DefasagemRiskPredictor(_make_artifact(np.array([[0.5, float("nan")]])))
        with pytest.raises(PredictionError, match="invalid probability"):
            predictor.predict(SAMPLE_COMMAND)
