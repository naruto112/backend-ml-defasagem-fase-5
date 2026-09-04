"""Flask application factory."""

import logging
from pathlib import Path

from flask import Flask

from app.api.defasagem_risk_record_routes import risk_record_blueprint
from app.api.domain_routes import domain_blueprint
from app.api.errors import register_error_handlers
from app.api.health_routes import health_blueprint
from app.api.middleware import configure_logging, register_request_middleware
from app.config import load_config
from app.extensions import api, db
from app.ml.model_loader import ModelArtifactError, load_model
from app.ml.predictor import DefasagemRiskPredictor
from app.schemas import DefasagemRiskRecordCreateSchema

logger = logging.getLogger(__name__)

DEFAULT_MODEL_PATH = str(
    Path(__file__).resolve().parent.parent / "artifacts" / "modelo_risco_defasagem.joblib"
)
DEFAULT_MANIFEST_PATH = str(
    Path(__file__).resolve().parent.parent
    / "artifacts"
    / "modelo_risco_defasagem.manifest.json"
)


def create_app(config_name: str | None = None) -> Flask:
    """Create the Flask application without touching external resources.

    Building the application never runs migrations, seeds, or database queries.
    """
    app = Flask(__name__)
    app.config.from_mapping(load_config(config_name))
    configure_logging(app)
    db.init_app(app)
    api.init_app(app)
    api.spec.components.schema(
        "DefasagemRiskRecordCreate",
        schema=DefasagemRiskRecordCreateSchema,
    )
    api.register_blueprint(health_blueprint)
    api.register_blueprint(domain_blueprint)
    api.register_blueprint(risk_record_blueprint)
    register_request_middleware(app)
    register_error_handlers(app)

    # Register model metadata for Alembic without touching the database.
    from app import models  # noqa: F401

    # Load ML model once per worker at startup.
    if not app.config.get("TESTING"):
        _bootstrap_ml(app)

    return app


def _bootstrap_ml(app: Flask) -> None:
    """Load and verify the ML model artifact, storing the predictor in app config."""
    import os

    model_path = Path(os.getenv("ML_MODEL_PATH", DEFAULT_MODEL_PATH))
    manifest_path = Path(os.getenv("ML_MANIFEST_PATH", DEFAULT_MANIFEST_PATH))

    try:
        model = load_model(model_path, manifest_path)
        predictor = DefasagemRiskPredictor(model)
        app.config["ML_PREDICTOR"] = predictor
        logger.info("ml_bootstrap_complete")
    except ModelArtifactError:
        logger.exception("ml_bootstrap_failed")
        raise


__all__ = ["create_app"]
