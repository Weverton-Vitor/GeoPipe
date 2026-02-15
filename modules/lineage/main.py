import uvicorn
from api.routes import images, runs, timeseries, artifacts
from config import API_TITLE, API_VERSION
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles


def create_app() -> FastAPI:
    """
    Application factory.
    Facilita testes e extensões futuras.
    """
    app = FastAPI(
        title=API_TITLE,
        version=API_VERSION,
    )

    # Rotas
    app.include_router(
        runs.router,
        prefix="/runs",
        tags=["Runs"],
    )
    app.include_router(
        timeseries.router,
        prefix="/timeseries",
        tags=["TimeSeries"],
    )
    app.include_router(
        images.router,
        prefix="/images",
        tags=["Images"],
    )

    app.include_router(
        artifacts.router,
        prefix="/artifacts",
        tags=["Artifacts"],
    )

    return app


app = create_app()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

BASE_DIR = Path(__file__).resolve().parents[2]  # ajuste se necessário

STATIC_IMAGES_DIR = BASE_DIR / "public" / "images"
STATIC_IMAGES_DIR.mkdir(parents=True, exist_ok=True)


app.mount("/static/images", StaticFiles(directory=STATIC_IMAGES_DIR), name="images")


def main():
    """
    Permite rodar:
        python -m geopipe.lineage.main
    ou
        geopipe lineage
    """
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8080,
        reload=True,
        log_level="info",
    )


if __name__ == "__main__":
    main()
