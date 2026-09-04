"""Problem responses and global error handlers."""

from __future__ import annotations

from http import HTTPStatus
from typing import Any

from flask import Flask, Response, g, json, request
from werkzeug.exceptions import HTTPException

from app.services import DefasagemRiskRecordNotFoundError, DomainNotFoundError

PROBLEM_BASE = "https://api.local/problems"


def problem_response(
    status: int,
    slug: str,
    title: str,
    detail: str,
    *,
    errors: list[dict[str, str]] | None = None,
) -> Response:
    body: dict[str, Any] = {
        "type": f"{PROBLEM_BASE}/{slug}",
        "title": title,
        "status": status,
        "detail": detail,
        "instance": request.path,
        "request_id": getattr(g, "request_id", ""),
    }
    if errors is not None:
        body["errors"] = errors
    return Response(json.dumps(body), status=status, content_type="application/problem+json")


def validation_problem(messages: dict[str, Any]) -> Response:
    errors: list[dict[str, str]] = []
    for field, field_messages in messages.items():
        values = field_messages if isinstance(field_messages, list) else ["invalid_type"]
        errors.extend({"field": field, "code": str(code), "message": str(code)} for code in values)
    return problem_response(
        422,
        "validation-error",
        "Payload invalido",
        "Um ou mais campos sao invalidos.",
        errors=errors,
    )


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(DomainNotFoundError)
    @app.errorhandler(DefasagemRiskRecordNotFoundError)
    def handle_not_found(error: Exception) -> Response:
        return problem_response(
            404, "not-found", "Recurso nao encontrado", "O recurso solicitado nao existe."
        )

    @app.errorhandler(HTTPException)
    def handle_http_error(error: HTTPException) -> Response:
        status = error.code or 500
        details = {
            400: ("invalid-json", "JSON invalido", "O corpo JSON esta vazio ou malformado."),
            404: ("not-found", "Recurso nao encontrado", "O recurso solicitado nao existe."),
            413: ("payload-too-large", "Corpo muito grande", "O corpo excede o limite."),
            415: ("unsupported-media-type", "Midia nao suportada", "Use application/json."),
        }
        slug, title, detail = details.get(
            status,
            ("http-error", HTTPStatus(status).phrase, "A requisicao nao pode ser processada."),
        )
        return problem_response(status, slug, title, detail)

    @app.errorhandler(Exception)
    def handle_unexpected_error(error: Exception) -> Response:
        app.logger.exception("unhandled_exception", extra={"exception_class": type(error).__name__})
        return problem_response(
            500, "internal-error", "Erro interno", "Ocorreu um erro interno inesperado."
        )
