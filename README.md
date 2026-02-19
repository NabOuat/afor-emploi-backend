# Emploi Backend API

FastAPI-based backend for the employment management system.

## Setup

### Prerequisites
- Python 3.8+
- PostgreSQL 12+

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables in `.env`:
```
DATABASE_URL=postgresql://user:password@localhost:5432/emploidb?client_encoding=utf8
SECRET_KEY=your-secret-key-here
```

3. Run the application:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

## API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Endpoints

### Authentication
- `POST /api/auth/login` - Login with username/password
- `POST /api/auth/register` - Register new user

### Geographic Data
- `GET/POST /api/geographic/regions` - Manage regions
- `GET/POST /api/geographic/departements` - Manage departments
- `GET/POST /api/geographic/sousprefectures` - Manage sub-prefectures

### Actors
- `GET/POST /api/acteurs` - Manage actors

### Projects
- `GET/POST /api/projets` - Manage projects

### Persons
- `GET/POST /api/personnes` - Manage persons

### Contracts
- `GET/POST /api/contrats` - Manage contracts

### Supervision
- `GET/POST /api/supervisions` - Manage supervision records

### Localization
- `GET/POST /api/localisations` - Manage person localization

### Intervention Zones
- `GET/POST /api/zones-intervention` - Manage intervention zones

## Database Schema

The database schema is defined in `scripts/create_tables.sql`. Tables include:
- Geographic hierarchy (regions, departments, sub-prefectures)
- Authentication (login, administrators)
- Actors and projects
- Person records with contracts and supervision
- Localization tracking

## Project Structure

```
afor-emploi-backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration settings
│   ├── database.py          # Database connection
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   ├── security.py          # Authentication & security
│   └── routes/
│       ├── auth.py          # Authentication endpoints
│       ├── geographic.py    # Geographic endpoints
│       ├── acteur.py        # Actor endpoints
│       ├── projet.py        # Project endpoints
│       ├── personne.py      # Person endpoints
│       ├── contrat.py       # Contract endpoints
│       ├── supervision.py   # Supervision endpoints
│       ├── localisation.py  # Localization endpoints
│       └── zone_intervention.py  # Intervention zone endpoints
├── main.py                  # Entry point
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Development

For development with auto-reload:
```bash
python main.py
```

For production, use a production ASGI server like Gunicorn:
```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app
```
