import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router

app = FastAPI(title="SupportIQ API", version="1.0.0",
              description="IT support analytics: SQL for filtering, Pandas for calculations.")

origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if o.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["GET", "POST"], allow_headers=["*"])

app.include_router(router)


@app.get("/")
def root():
    return {"name": "SupportIQ API", "docs": "/docs"}
