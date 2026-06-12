# -*- coding: utf-8 -*-
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, RedirectResponse
from app.database import init_db
from app.config import settings
from app.routes import auth, geographic, acteur, projet, personne, contrat, supervision, localisation, zone_intervention, user_actions, dashboard, import_export, employees, employees_create, zones, engagement, engagement_liaison, dashboard_responsible, admin_tools, data_import
from app.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # ── Startup ──────────────────────────────────────────────
    init_db()
    start_scheduler()
    yield
    # ── Shutdown ─────────────────────────────────────────────
    stop_scheduler()


openapi_tags = [
    {"name": "Authentification", "description": "Connexion, inscription et gestion des tokens d'accès"},
    {"name": "Utilisateurs",     "description": "Gestion des comptes utilisateurs et actions utilisateur"},
    {"name": "Acteurs",          "description": "Acteurs de la plateforme (opérateurs, AFOR, écoles…)"},
    {"name": "Employés",         "description": "Gestion des employés (fiches personnelles, création, recherche)"},
    {"name": "Contrats",         "description": "Contrats de travail des employés"},
    {"name": "Localisation",     "description": "Données géographiques (régions, départements, sous-préfectures) et localisations"},
    {"name": "Zones",            "description": "Zones d'intervention et supervisions"},
    {"name": "Projets",          "description": "Gestion des projets"},
    {"name": "Tableau de bord",  "description": "Statistiques et indicateurs"},
    {"name": "Import / Export",  "description": "Import/export de données (Excel, CSV)"},
    {"name": "Admin Tools",      "description": "Outils d'administration : inspection BD, correction encodage, export SQL, migration (admin uniquement)"},
    {"name": "Info",             "description": "Informations sur l'API et état du serveur"}
]

app = FastAPI(
    title="AFOR Emploi API",
    description="""
    ## Plateforme de Gestion du Personnel
    
    **AGENCE FONCIÈRE RURALE (AFOR)**
    
    API complète pour la gestion du personnel, des contrats, des zones d'intervention et des projets.
    
    ### Fonctionnalités principales
    - **Authentification** sécurisée avec JWT
    - **Gestion des employés** et acteurs
    - **Contrats de travail** et engagements
    - **Localisation** et zones d'intervention
    - **Tableaux de bord** et statistiques
    - **Import/Export** de données
    - **Outils d'administration**
    
    ### Quick Start
    1. Utilisez l'endpoint `/api/auth/login` pour obtenir un token
    2. Ajoutez le token dans l'en-tête `Authorization: Bearer <token>`
    3. Explorez les endpoints disponibles ci-dessous
    
    ---
    **Version**: 1.0.0 | **Base URL**: http://localhost:8000
    """,
    version="1.0.0",
    openapi_tags=openapi_tags,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Headers de sécurité sur toutes les réponses ───────────────────────────────
@app.middleware("http")
async def add_security_headers(request: Request, call_next) -> Response:
    response = await call_next(request)
    response.headers["X-Content-Type-Options"]    = "nosniff"
    response.headers["X-Frame-Options"]           = "DENY"
    response.headers["Referrer-Policy"]           = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"]        = "geolocation=(), microphone=(), camera=()"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

# ── Routes organisées par ordre d'importance ────────────────────────────────
# 1. Authentification et utilisateurs
app.include_router(auth.router)
app.include_router(user_actions.router)

# 2. Acteurs et employés
app.include_router(acteur.router)
app.include_router(employees.router)
app.include_router(employees_create.router)
app.include_router(personne.router)

# 3. Contrats et engagements
app.include_router(contrat.router)
app.include_router(engagement.router)
app.include_router(engagement_liaison.router)

# 4. Projets
app.include_router(projet.router)

# 5. Localisation et zones
app.include_router(geographic.router)
app.include_router(localisation.router)
app.include_router(zone_intervention.router)
app.include_router(zones.router)
app.include_router(supervision.router)

# 6. Tableau de bord et statistiques
app.include_router(dashboard.router)
app.include_router(dashboard_responsible.router)

# 7. Import / Export
app.include_router(import_export.router)
app.include_router(data_import.router)

# 8. Outils administration
app.include_router(admin_tools.router)


# ── Routes racine ────────────────────────────────────────────────
@app.get("/", tags=["Info"])
async def root():
    """Redirection vers la documentation Swagger"""
    return RedirectResponse(url="/docs")


@app.get("/health", tags=["Info"])
async def health_check():
    """
    Vérification de l'état du serveur
    
    Retourne l'état de santé de l'API et les liens utiles
    """
    return {
        "status": "healthy",
        "service": "AFOR Emploi API",
        "version": "1.0.0",
        "timestamp": "2024-06-12",
        "environment": "development",
        "links": {
            "swagger_ui": "/docs",
            "redoc": "/redoc",
            "openapi_schema": "/openapi.json",
            "health_check": "/health"
        },
        "endpoints": {
            "auth": "/api/auth/login",
            "users": "/api/users",
            "employees": "/api/employees",
            "actors": "/api/actors"
        }
    }
