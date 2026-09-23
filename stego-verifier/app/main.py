"""FastAPI application entry point.

Run with:  uvicorn app.main:app --reload
"""

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import keys, media, protect, verify
from app.config import STATIC_DIR
from app.core.errors import StegoError

APP_TITLE = "P1-4 ACW1"
INDEX_FILE = "index.html"
STATIC_ROUTE = "/static"
BAD_REQUEST_STATUS = 400


def create_app() -> FastAPI:
    application = FastAPI(title=APP_TITLE)
    for router_module in (keys, protect, verify, media):
        application.include_router(router_module.router)
    application.add_exception_handler(StegoError, _handle_stego_error)
    application.mount(STATIC_ROUTE, StaticFiles(directory=STATIC_DIR), name="static")
    application.add_api_route("/", _serve_index, include_in_schema=False)
    return application


async def _handle_stego_error(_request: Request, error: StegoError) -> JSONResponse:
    return JSONResponse(status_code=BAD_REQUEST_STATUS, content={"detail": str(error)})


async def _serve_index() -> FileResponse:
    return FileResponse(STATIC_DIR / INDEX_FILE)


app = create_app()
