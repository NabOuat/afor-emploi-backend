# -*- coding: utf-8 -*-
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db
from app.config import settings
from app.routes import auth, geographic, acteur, projet, personne, contrat, supervision, localisation, zone_intervention, user_actions, dashboard, import_export, employees, employees_create, zones, engagement, engagement_liaison, dashboard_responsible
from app.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # ── Startup ──────────────────────────────────────────────
    init_db()
    start_scheduler()
    yield
    # ── Shutdown ─────────────────────────────────────────────
    stop_scheduler()


app = FastAPI(
    title="Emploi API",
    description="API for employment management system",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(geographic.router)
app.include_router(acteur.router)
app.include_router(projet.router)
app.include_router(personne.router)
app.include_router(contrat.router)
app.include_router(supervision.router)
app.include_router(localisation.router)
app.include_router(zone_intervention.router)
app.include_router(user_actions.router)
app.include_router(dashboard.router)
app.include_router(dashboard_responsible.router)
app.include_router(import_export.router)
app.include_router(employees.router)
app.include_router(employees_create.router)
app.include_router(zones.router)
app.include_router(engagement.router)
app.include_router(engagement_liaison.router)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
