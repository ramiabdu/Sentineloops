from fastapi import status


class AppError(Exception):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    code = "internal_error"
    message = "An unexpected error occurred."

    def __init__(self, *, code: str | None = None, message: str | None = None) -> None:
        self.code = code or self.code
        self.message = message or self.message
        super().__init__(self.message)


class ConflictError(AppError):
    status_code = status.HTTP_409_CONFLICT
    code = "conflict"
    message = "The request conflicts with the current resource state."


class NotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    code = "not_found"
    message = "The requested resource was not found."


class AuthenticationError(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED
    code = "authentication_failed"
    message = "Valid bearer authentication is required."
