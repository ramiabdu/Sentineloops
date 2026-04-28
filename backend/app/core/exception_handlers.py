from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.errors import AppError
from app.schemas.errors import ErrorDetail, ErrorResponse, ValidationErrorResponse


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)


async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    response = ErrorResponse(code=exc.code, message=exc.message)
    return JSONResponse(status_code=exc.status_code, content=response.model_dump())


async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    response = ValidationErrorResponse(
        code="validation_error",
        message="Request validation failed.",
        details=[
            ErrorDetail(
                loc=list(error.get("loc", ())),
                message=error.get("msg", "Invalid value."),
                type=error.get("type", "value_error"),
            )
            for error in exc.errors()
        ],
    )
    return JSONResponse(
        status_code=422,
        content=response.model_dump(),
    )
