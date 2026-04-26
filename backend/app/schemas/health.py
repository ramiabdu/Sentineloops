from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str


class RootResponse(BaseModel):
    service: str
    environment: str
    debug: bool
    status: str
