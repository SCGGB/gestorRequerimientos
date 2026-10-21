"""Documentacion de respuestas de error en el esquema OpenAPI.

El envelope real lo produce `app.api.errors`; aqui solo se describe en OpenAPI
(`401`, `403`, `404`, `409`) con el esquema `ErrorResponse` y un ejemplo por
codigo de error.
"""

from __future__ import annotations

from typing import Any

from app.api.schemas.errors import ErrorResponse


def _envelope(code: str, message: str) -> dict[str, Any]:
    return {"error": {"code": code, "message": message}}


def error_response(
    description: str,
    examples: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Construye una respuesta OpenAPI con el envelope de error compartido."""
    return {
        "model": ErrorResponse,
        "description": description,
        "content": {
            "application/json": {
                "examples": {
                    name: {"value": value} for name, value in examples.items()
                }
            }
        },
    }


UNAUTHENTICATED_RESPONSE = error_response(
    "Sesion ausente, invalida o expirada.",
    {
        "unauthenticated": _envelope(
            "unauthenticated",
            "No hay una sesion valida. Inicia sesion nuevamente.",
        )
    },
)

INVALID_CREDENTIALS_RESPONSE = error_response(
    "Credenciales invalidas o cuenta bloqueada por intentos fallidos.",
    {
        "invalid_credentials": _envelope(
            "invalid_credentials",
            "Las credenciales no son validas.",
        ),
        "account_locked": _envelope(
            "account_locked",
            "La cuenta esta bloqueada por intentos fallidos.",
        ),
    },
)

FORBIDDEN_RESPONSE = error_response(
    "El rol autenticado no tiene permiso para la operacion.",
    {
        "forbidden": _envelope(
            "forbidden",
            "Acceso denegado para el rol autenticado.",
        )
    },
)


def not_found_response(code: str, message: str) -> dict[str, Any]:
    """Respuesta `404` con el envelope de error compartido."""
    return error_response("El recurso solicitado no existe.", {code: _envelope(code, message)})


def conflict_response(code: str, message: str) -> dict[str, Any]:
    """Respuesta `409` con el envelope de error compartido."""
    return error_response(
        "La operacion entra en conflicto con el estado actual del recurso.",
        {code: _envelope(code, message)},
    )
