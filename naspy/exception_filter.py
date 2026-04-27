from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

HTTP_STATUS_MESSAGES = {
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    409: "Conflict",
    422: "Unprocessable Entity",
    500: "Internal Server Error",
}

def register_exception_filters(app: FastAPI):

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "outcome": False,
                "error": {
                    "code": exc.status_code,
                    "status": HTTP_STATUS_MESSAGES.get(exc.status_code, "Unknown Error"),
                    "message": exc.detail
                }
            }
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={
                "outcome": False,
                "error": {
                    "code": 422,
                    "status": "Unprocessable Entity",
                    "message": exc.errors()[0]["msg"] if exc.errors() else "Validation error"
                }
            }
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={
                "outcome": False,
                "error": {
                    "code": 500,
                    "status": "Internal Server Error",
                    "message": str(exc)
                }
            }
        )