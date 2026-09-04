"""Predict PEDE defasagem-risk probability and risk band."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np

from app.ml.feature_transformer import FEATURE_COLUMNS, FeatureTransformer

DEFAULT_RISK_BANDS: tuple[tuple[str, float, float, str], ...] = (
    ("Baixo", 0.00, 0.25, "Sem sinal de alerta"),
    ("M\u00e9dio", 0.25, 0.50, "Monitorar no pr\u00f3ximo ciclo"),
    ("Alto", 0.50, 1.01, "Prioridade de acompanhamento"),
)


class PredictionError(RuntimeError):
    """The model returned an unexpected prediction."""


class DefasagemRiskPredictor:
    """Combine feature preparation, model inference, and risk-band classification."""

    def __init__(
        self,
        artifact: Mapping[str, Any],
        transformer: FeatureTransformer | None = None,
    ) -> None:
        self._model = artifact["modelo"]
        self._features = list(artifact.get("features", FEATURE_COLUMNS))
        self._risk_bands = self._normalize_risk_bands(
            artifact.get("faixas_risco", DEFAULT_RISK_BANDS)
        )
        self._transformer = transformer or FeatureTransformer()

    def predict(self, command: Mapping[str, Any]) -> dict[str, Any]:
        features = self._transformer.transform(command)
        raw_probabilities = self._model.predict_proba(features[self._features])
        probabilities = np.asarray(raw_probabilities)

        if probabilities.shape != (1, 2):
            raise PredictionError("Model returned unexpected probability shape")

        probability = float(probabilities[0, 1])
        if not np.isfinite(probability) or probability < 0 or probability > 1:
            raise PredictionError(f"Model returned invalid probability: {probability}")

        risk_band, suggested_action = self._classify_risk(probability)
        return {
            "probabilidade": probability,
            "faixa_risco": risk_band,
            "acao_sugerida": suggested_action,
        }

    @staticmethod
    def _normalize_risk_bands(value: Any) -> tuple[tuple[str, float, float, str], ...]:
        bands: list[tuple[str, float, float, str]] = []
        for item in value if isinstance(value, Sequence) else DEFAULT_RISK_BANDS:
            name, lower, upper, action = item
            bands.append((str(name), float(lower), float(upper), str(action)))
        return tuple(bands)

    def _classify_risk(self, probability: float) -> tuple[str, str]:
        for name, lower, upper, action in self._risk_bands:
            if lower <= probability < upper:
                return name, action
        return "Alto", "Prioridade de acompanhamento"
