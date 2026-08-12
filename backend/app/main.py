import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import router

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Corretor OMR",
    description="API de correção automática de cartões-resposta (OMR)",
    version="0.1.0",
)

# CORS liberado para desenvolvimento local (frontend em outra porta/Vite dev server)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
def root():
    return {"app": "Corretor OMR", "status": "running", "docs": "/docs"}
