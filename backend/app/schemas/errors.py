from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    loc: list[str | int] = Field(default_factory=list)
    message: str
    type: str


class ErrorResponse(BaseModel):
    code: str
    message: str


class ValidationErrorResponse(ErrorResponse):
    details: list[ErrorDetail] = Field(default_factory=list)
