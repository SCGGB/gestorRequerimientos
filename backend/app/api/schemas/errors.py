from typing import Any

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Any = Field(default=None)


class ErrorResponse(BaseModel):
    error: ErrorDetail
