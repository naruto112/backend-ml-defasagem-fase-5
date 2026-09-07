"""Request correlation and payload-free access logs."""

from __future__ import annotations

import json
import logging
import re
import time
from datetime import datetime, timezone
from uuid import uuid4

from flask import Flask, Response, g, request

REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "level": record.levelname,
            "event": record.getMessage(),
        }
        for key in (
            "request_id",
            "method",
            "route",
            "status",
            "duration_ms",
            "exception_class",
        ):
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value
        if record.exc_info and record.exc_info[1] is not None:
            payload["exception_message"] = str(record.exc_info[1]).splitlines()[0]
        return json.dumps(payload, ensure_ascii=True)


def configure_logging(app: Flask) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    app.logger.handlers.clear()
    app.logger.addHandler(handler)
    app.logger.setLevel(app.config["LOG_LEVEL"])
    app.logger.propagate = False


def register_request_middleware(app: Flask) -> None:
    @app.before_request
    def start_request() -> None:
        supplied = request.headers.get("X-Request-ID", "")
        g.request_id = supplied if REQUEST_ID_PATTERN.fullmatch(supplied) else str(uuid4())
        g.request_started = time.perf_counter()

    @app.after_request
    def finish_request(response: Response) -> Response:
        request_id = getattr(g, "request_id", str(uuid4()))
        response.headers["X-Request-ID"] = request_id
        route = request.url_rule.rule if request.url_rule is not None else request.path
        started = getattr(g, "request_started", time.perf_counter())
        app.logger.info(
            "http_request",
            extra={
                "request_id": request_id,
                "method": request.method,
                "route": route,
                "status": response.status_code,
                "duration_ms": round((time.perf_counter() - started) * 1000, 3),
            },
        )
        return response
