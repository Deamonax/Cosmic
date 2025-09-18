from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from db import init_db
from routers.core import router as core_router
from routers.upload import router as upload_router

app = FastAPI(title="JobFit API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


STORAGE_DIR = Path(__file__).resolve().parent / "storage"


@app.on_event("startup")
def ensure_storage_and_tables() -> None:
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    init_db()


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content={
            "message": "Invalid request payload",
            "errors": exc.errors(),
        },
    )


app.include_router(core_router)
app.include_router(upload_router, prefix="/upload")
