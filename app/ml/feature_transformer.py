"""Build the raw PEDE feature DataFrame expected by the exported pipeline."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pandas as pd

from app.domain_catalog import INPUT_FIELDS

FEATURE_COLUMNS: list[str] = list(INPUT_FIELDS)


class FeatureTransformer:
    """Convert a validated API command into a single-row DataFrame with 12 raw features."""

    def transform(self, command: Mapping[str, Any]) -> pd.DataFrame:
        row: dict[str, int | float | str] = {
            "defasagem": int(command["defasagem"]),
            "fase_ordem": int(command["fase_ordem"]),
            "idade": int(command["idade"]),
            "ano_ingresso": int(command["ano_ingresso"]),
            "ida": float(command["ida"]),
            "ieg": float(command["ieg"]),
            "iaa": float(command["iaa"]),
            "ips": float(command["ips"]),
            "ipv": float(command["ipv"]),
            "inde": float(command["inde"]),
            "genero": str(command["genero"]),
            "instituicao": str(command["instituicao"]),
        }

        return pd.DataFrame([row], columns=FEATURE_COLUMNS)
