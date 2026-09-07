"""Tests for app.ml package (feature_transformer, model_loader, predictor)."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from app.ml.feature_transformer import FEATURE_COLUMNS, FeatureTransformer
from app.ml.model_loader import ModelArtifactError, _sha256, load_model, verify_artifact
from app.ml.predictor import DefasagemRiskPredictor, PredictionError

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


class TestFeatureTransformer:
    def test_output_shape_and_columns(self):
        transformer = FeatureTransformer()
        df = transformer.transform(SAMPLE_COMMAND)
        assert isinstance(df, pd.DataFrame)
        assert list(df.columns) == FEATURE_COLUMNS
        assert len(df) == 1

    def test_genero_encoding(self):
        transformer = FeatureTransformer()
        masculino_cmd = {**SAMPLE_COMMAND, "genero": "masculino"}
        feminino_cmd = {**SAMPLE_COMMAND, "genero": "feminino"}
        assert transformer.transform(masculino_cmd)["genero_masculino"].iloc[0] == 1
        assert transformer.transform(feminino_cmd)["genero_masculino"].iloc[0] == 0

    def test_instituicao_encoding(self):
        transformer = FeatureTransformer()
        publica_cmd = {**SAMPLE_COMMAND, "instituicao": "publica"}
        privada_cmd = {**SAMPLE_COMMAND, "instituicao": "privada"}
        assert transformer.transform(publica_cmd)["instituicao_publica"].iloc[0] == 1
        assert transformer.transform(privada_cmd)["instituicao_publica"].iloc[0] == 0

    def test_pedra_ordinal_encoding(self):
        transformer = FeatureTransformer()
        cmd = {**SAMPLE_COMMAND, "pedra": "quartil_1"}
        df = transformer.transform(cmd)
        assert df["pedra"].iloc[0] == 0  # quartil_1 mapeado para 0


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

    def test_load_model_type_mismatch(self, tmp_path: Path):
        import joblib

        model_file = tmp_path / "model.joblib"
        joblib.dump(SimpleNamespace(), model_file)
        real_sha = _sha256(model_file)
        manifest_file = tmp_path / "manifest.json"
        manifest_file.write_text(
            json.dumps(
                {
                    "sha256": real_sha,
                    "size_bytes": model_file.stat().st_size,
                    "algorithm": "HistGradientBoostingClassifier",
                }
            )
        )
        with pytest.raises(ModelArtifactError, match="Model type mismatch"):
            load_model(model_file, manifest_file)

    def test_load_model_success_no_algorithm_check(self, tmp_path: Path):
        import joblib

        model_file = tmp_path / "model.joblib"
        joblib.dump(SimpleNamespace(), model_file)
        real_sha = _sha256(model_file)
        manifest_file = tmp_path / "manifest.json"
        manifest_file.write_text(
            json.dumps({"sha256": real_sha, "size_bytes": model_file.stat().st_size})
        )
        result = load_model(model_file, manifest_file)
        assert result is not None


class TestDefasagemRiskPredictor:
    def _make_model(self, proba_return_value):
        class FakeModel:
            def predict_proba(self, X):
                return proba_return_value

        return FakeModel()

    def test_predict_returns_dict_with_probability_and_action(self):
        model = self._make_model(np.array([[0.3, 0.7]]))
        predictor = DefasagemRiskPredictor(model)
        result = predictor.predict(SAMPLE_COMMAND)
        assert "probabilidade" in result
        assert "faixa_risco" in result
        assert "acao_sugerida" in result
        assert isinstance(result["probabilidade"], float)

    def test_predict_with_high_probability(self):
        model = self._make_model(np.array([[0.2, 0.8]]))
        predictor = DefasagemRiskPredictor(model)
        result = predictor.predict(SAMPLE_COMMAND)
        assert result["probabilidade"] == 0.8

    def test_predict_with_low_probability(self):
        model = self._make_model(np.array([[0.9, 0.1]]))
        predictor = DefasagemRiskPredictor(model)
        result = predictor.predict(SAMPLE_COMMAND)
        assert result["probabilidade"] == 0.1

    def test_predict_unexpected_shape_raises(self):
        model = self._make_model(np.array([[0.5, 0.5], [0.5, 0.5]]))
        predictor = DefasagemRiskPredictor(model)
        with pytest.raises(PredictionError, match="unexpected output shape"):
            predictor.predict(SAMPLE_COMMAND)

    def test_predict_none_raises(self):
        model = self._make_model(None)
        predictor = DefasagemRiskPredictor(model)
        with pytest.raises(PredictionError, match="unexpected output shape"):
            predictor.predict(SAMPLE_COMMAND)
