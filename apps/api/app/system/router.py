"""Process liveness; no database, provider, or settings dependency."""

from typing import Literal

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.core.errors import error_response

router = APIRouter(prefix="/health", tags=["System"])


class LivenessData(BaseModel):
    status: Literal["ok"]


class LivenessResponse(BaseModel):
    data: LivenessData


@router.get(
    "/live",
    response_model=LivenessResponse,
    summary="Check process liveness",
    responses={422: {"description": "Unsupported query parameters; sanitized error"}},
)
def health_live(request: Request) -> LivenessResponse | JSONResponse:
    if request.query_params:
        return error_response(
            request, 422, "validation_error", "Request validation failed",
            [{"field": "query", "code": "unsupported_query_parameter",
              "message": "Query parameters are not supported"}],
        )

    return LivenessResponse(data=LivenessData(status="ok"))
