from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware

from app.data_loader import store
from app.routers import district, habitations, layers, recommend

app = FastAPI(
    title="RedZone DSS API",
    description="AI-assisted, explainable GIS decision-support prototype for Rudraprayag hazard-based red zones and relocation planning.",
    version="1.0.0",
)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    store.load()


app.include_router(district.router, prefix="/api", tags=["district"])
app.include_router(habitations.router, prefix="/api/habitations", tags=["habitations"])
app.include_router(layers.router, prefix="/api/layers", tags=["layers"])
app.include_router(recommend.router, prefix="/api", tags=["recommendation"])
