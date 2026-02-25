# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from datetime import date, timedelta
from app.database import get_db
from app.models import (
    FicPersonne, Contrat, FicPersonneLocalisation,
    FicPersonneProjet, Projet, TRegion
)

router = APIRouter(prefix="/api/dashboard/responsible", tags=["dashboard_responsible"])


def _base_query(db: Session, acteur_id: str, filter_type: str = "tous"):
    """Retourne une liste de tuples (FicPersonne, Contrat) filtrés par acteur."""
    today = date.today()

    q = (
        db.query(FicPersonne, Contrat)
        .join(FicPersonneProjet, FicPersonne.id == FicPersonneProjet.fic_personne_id)
        .join(Contrat, FicPersonne.id == Contrat.fic_personne_id)
        .filter(FicPersonneProjet.acteur_id == acteur_id)
    )

    if filter_type == "actifs":
        q = q.filter(
            Contrat.date_debut <= today,
            or_(Contrat.date_fin >= today, Contrat.date_fin.is_(None))
        )
    elif filter_type == "inactifs":
        q = q.filter(Contrat.date_fin < today)

    return q.distinct(FicPersonne.id).all()


def _calc_age(date_naissance) -> int:
    if not date_naissance:
        return 0
    today = date.today()
    age = today.year - date_naissance.year
    if (today.month, today.day) < (date_naissance.month, date_naissance.day):
        age -= 1
    return age


# ─────────────────────────────────────────────────────────────
# 1. Statistiques générales
# ─────────────────────────────────────────────────────────────
@router.get("/statistics/{acteur_id}")
async def get_responsible_statistics(
    acteur_id: str, filter_type: str = "tous", db: Session = Depends(get_db)
):
    """Statistiques RH complètes : effectif, contrats, genre, âge, ratio, durée moyenne."""
    try:
        today = date.today()
        rows = _base_query(db, acteur_id, filter_type)

        total = len(rows)
        cdi = sum(1 for _, c in rows if c.type_contrat == "CDI")
        cdd = sum(1 for _, c in rows if c.type_contrat == "CDD")
        consultant = sum(1 for _, c in rows if c.type_contrat == "Consultant")
        hommes = sum(1 for p, _ in rows if p.genre == "M")
        femmes = sum(1 for p, _ in rows if p.genre == "F")

        ages = [_calc_age(p.date_naissance) for p, _ in rows if p.date_naissance]
        age_min = min(ages) if ages else 0
        age_max = max(ages) if ages else 0
        age_moy = round(sum(ages) / len(ages)) if ages else 0

        actifs = sum(
            1 for _, c in rows
            if c.date_debut and c.date_debut <= today
            and (c.date_fin is None or c.date_fin >= today)
        )
        expires = total - actifs

        durations = [
            (c.date_fin - c.date_debut).days // 30
            for _, c in rows
            if c.date_debut and c.date_fin
        ]
        avg_duration = round(sum(durations) / len(durations)) if durations else 0

        permanent = cdi
        temporaire = cdd + consultant

        return {
            "totalEmployes": total,
            "cdi": cdi,
            "cdd": cdd,
            "consultant": consultant,
            "hommes": hommes,
            "femmes": femmes,
            "tauxFeminisation": round(femmes * 100 / total) if total else 0,
            "ageMin": age_min,
            "ageMax": age_max,
            "ageMoyen": age_moy,
            "contratsActifs": actifs,
            "contratsExpires": expires,
            "tauxRenouvellement": round(expires * 100 / total) if total else 0,
            "ratioPermanentTemporaire": f"{permanent}/{temporaire}",
            "dureemoyenneContrats": avg_duration,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────
# 2. Contrats arrivant à échéance
# ─────────────────────────────────────────────────────────────
@router.get("/contrats-echeance/{acteur_id}")
async def get_contracts_expiring(acteur_id: str, db: Session = Depends(get_db)):
    """Contrats expiriant dans 3 mois, 6 mois et 12 mois."""
    try:
        today = date.today()
        d3  = today + timedelta(days=90)
        d6  = today + timedelta(days=180)
        d12 = today + timedelta(days=365)

        def count_range(start, end):
            return (
                db.query(func.count(Contrat.id))
                .join(FicPersonne, Contrat.fic_personne_id == FicPersonne.id)
                .join(FicPersonneProjet, FicPersonne.id == FicPersonneProjet.fic_personne_id)
                .filter(
                    FicPersonneProjet.acteur_id == acteur_id,
                    Contrat.date_debut <= today,
                    Contrat.date_fin > start,
                    Contrat.date_fin <= end,
                )
                .scalar() or 0
            )

        return {
            "dans3mois":  count_range(today, d3),
            "dans6mois":  count_range(d3,    d6),
            "dans12mois": count_range(d6,    d12),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────
# 3. Effectif par région
# ─────────────────────────────────────────────────────────────
@router.get("/effectif-par-region/{acteur_id}")
async def get_employees_by_region(
    acteur_id: str, filter_type: str = "tous", db: Session = Depends(get_db)
):
    """Effectif déployé par région géographique."""
    try:
        today = date.today()

        q = (
            db.query(TRegion.nom, func.count(FicPersonne.id.distinct()).label("effectif"))
            .join(FicPersonneLocalisation, TRegion.id == FicPersonneLocalisation.region_id)
            .join(Contrat, FicPersonneLocalisation.contrat_id == Contrat.id)
            .join(FicPersonne, Contrat.fic_personne_id == FicPersonne.id)
            .join(FicPersonneProjet, FicPersonne.id == FicPersonneProjet.fic_personne_id)
            .filter(FicPersonneProjet.acteur_id == acteur_id)
        )

        if filter_type == "actifs":
            q = q.filter(
                Contrat.date_debut <= today,
                or_(Contrat.date_fin >= today, Contrat.date_fin.is_(None))
            )
        elif filter_type == "inactifs":
            q = q.filter(Contrat.date_fin < today)

        results = q.group_by(TRegion.nom).all()
        total = sum(r[1] for r in results)

        return sorted(
            [
                {
                    "region": r[0] or "Non spécifiée",
                    "effectif": r[1],
                    "pourcentage": round(r[1] * 100 / total) if total else 0,
                }
                for r in results
            ],
            key=lambda x: x["effectif"],
            reverse=True,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────
# 4. Évolution des effectifs (12 derniers mois)
# ─────────────────────────────────────────────────────────────
@router.get("/evolution-effectifs/{acteur_id}")
async def get_evolution_effectifs(
    acteur_id: str, months: int = 12, db: Session = Depends(get_db)
):
    """Évolution mensuelle des effectifs actifs sur les N derniers mois."""
    try:
        today = date.today()
        result = []

        for i in range(months - 1, -1, -1):
            # Premier jour du mois i mois en arrière
            month_date = (today.replace(day=1) - timedelta(days=i * 30)).replace(day=1)

            count = (
                db.query(func.count(FicPersonne.id.distinct()))
                .join(FicPersonneProjet, FicPersonne.id == FicPersonneProjet.fic_personne_id)
                .join(Contrat, FicPersonne.id == Contrat.fic_personne_id)
                .filter(
                    FicPersonneProjet.acteur_id == acteur_id,
                    Contrat.date_debut <= month_date,
                    or_(Contrat.date_fin >= month_date, Contrat.date_fin.is_(None)),
                )
                .scalar() or 0
            )

            result.append({
                "mois": month_date.strftime("%b %y"),
                "effectif": count,
            })

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────
# 5. Taux d'occupation par projet
# ─────────────────────────────────────────────────────────────
@router.get("/taux-occupation-projets/{acteur_id}")
async def get_projects_occupation_rate(
    acteur_id: str, filter_type: str = "tous", db: Session = Depends(get_db)
):
    """Nombre d'employés par projet et taux d'occupation estimé."""
    try:
        today = date.today()

        q = (
            db.query(Projet.nom, func.count(FicPersonne.id.distinct()).label("count"))
            .join(FicPersonneProjet, Projet.id == FicPersonneProjet.projet_id)
            .join(FicPersonne, FicPersonneProjet.fic_personne_id == FicPersonne.id)
            .join(Contrat, FicPersonne.id == Contrat.fic_personne_id)
            .filter(FicPersonneProjet.acteur_id == acteur_id)
        )

        if filter_type == "actifs":
            q = q.filter(
                Contrat.date_debut <= today,
                or_(Contrat.date_fin >= today, Contrat.date_fin.is_(None))
            )
        elif filter_type == "inactifs":
            q = q.filter(Contrat.date_fin < today)

        results = q.group_by(Projet.nom).all()

        return sorted(
            [
                {
                    "nomProjet": r[0] or "Non spécifié",
                    "nombrePersonnes": r[1],
                    "capaciteMax": max(int(r[1] * 1.2), 1),
                    "tauxOccupation": min(int(r[1] / max(int(r[1] * 1.2), 1) * 100), 100),
                }
                for r in results
            ],
            key=lambda x: x["nombrePersonnes"],
            reverse=True,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────
# 6. Répartition par genre
# ─────────────────────────────────────────────────────────────
@router.get("/genre/{acteur_id}")
async def get_gender_distribution(
    acteur_id: str, filter_type: str = "tous", db: Session = Depends(get_db)
):
    """Répartition Hommes / Femmes."""
    try:
        rows = _base_query(db, acteur_id, filter_type)
        total = len(rows)

        counts: dict = {}
        for p, _ in rows:
            g = p.genre or "Non spécifié"
            counts[g] = counts.get(g, 0) + 1

        return [
            {
                "genre": k,
                "nombre": v,
                "pourcentage": round(v * 100 / total) if total else 0,
            }
            for k, v in sorted(counts.items(), key=lambda x: x[1], reverse=True)
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────
# 7. Groupes d'âge
# ─────────────────────────────────────────────────────────────
@router.get("/groupes-age/{acteur_id}")
async def get_age_groups(
    acteur_id: str, filter_type: str = "tous", db: Session = Depends(get_db)
):
    """Distribution par tranche d'âge."""
    try:
        rows = _base_query(db, acteur_id, filter_type)

        groups = {
            "< 25 ans": 0,
            "25-34 ans": 0,
            "35-44 ans": 0,
            "45-54 ans": 0,
            "> 55 ans": 0,
        }
        total = 0

        for p, _ in rows:
            age = _calc_age(p.date_naissance)
            if age <= 0:
                continue
            total += 1
            if age < 25:
                groups["< 25 ans"] += 1
            elif age < 35:
                groups["25-34 ans"] += 1
            elif age < 45:
                groups["35-44 ans"] += 1
            elif age < 55:
                groups["45-54 ans"] += 1
            else:
                groups["> 55 ans"] += 1

        return [
            {
                "tranche": k,
                "nombre": v,
                "pourcentage": round(v * 100 / total) if total else 0,
            }
            for k, v in groups.items()
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────
# 8. Types de contrats
# ─────────────────────────────────────────────────────────────
@router.get("/types-contrats/{acteur_id}")
async def get_contract_types(
    acteur_id: str, filter_type: str = "tous", db: Session = Depends(get_db)
):
    """Répartition CDI / CDD / Consultant."""
    try:
        rows = _base_query(db, acteur_id, filter_type)
        total = len(rows)

        counts: dict = {}
        for _, c in rows:
            t = c.type_contrat or "Non spécifié"
            counts[t] = counts.get(t, 0) + 1

        return [
            {
                "type": k,
                "nombre": v,
                "pourcentage": round(v * 100 / total) if total else 0,
            }
            for k, v in sorted(counts.items(), key=lambda x: x[1], reverse=True)
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────
# 9. Niveau d'éducation (diplôme — champ sur Contrat)
# ─────────────────────────────────────────────────────────────
@router.get("/niveau-education/{acteur_id}")
async def get_education_levels(
    acteur_id: str, filter_type: str = "tous", db: Session = Depends(get_db)
):
    """Répartition par niveau d'éducation (diplôme)."""
    try:
        rows = _base_query(db, acteur_id, filter_type)
        total = len(rows)

        counts: dict = {}
        for _, c in rows:
            d = c.diplome or "Non spécifié"
            counts[d] = counts.get(d, 0) + 1

        return [
            {
                "niveau": k,
                "nombre": v,
                "pourcentage": round(v * 100 / total) if total else 0,
            }
            for k, v in sorted(counts.items(), key=lambda x: x[1], reverse=True)
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────
# 10. Employés par poste (champ sur Contrat)
# ─────────────────────────────────────────────────────────────
@router.get("/employes-par-poste/{acteur_id}")
async def get_employees_by_position(
    acteur_id: str, filter_type: str = "tous", db: Session = Depends(get_db)
):
    """Répartition des employés par poste (poste_nom sur Contrat)."""
    try:
        rows = _base_query(db, acteur_id, filter_type)
        total = len(rows)

        counts: dict = {}
        for _, c in rows:
            p = c.poste_nom or "Non spécifié"
            counts[p] = counts.get(p, 0) + 1

        return [
            {
                "poste": k,
                "nombre": v,
                "pourcentage": round(v * 100 / total) if total else 0,
            }
            for k, v in sorted(counts.items(), key=lambda x: x[1], reverse=True)
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────
# 11. Embauches mensuelles (12 derniers mois)
# ─────────────────────────────────────────────────────────────
@router.get("/embauches-mensuelles/{acteur_id}")
async def get_monthly_hires(
    acteur_id: str, months: int = 12, db: Session = Depends(get_db)
):
    """Embauches par mois sur les N derniers mois."""
    try:
        today = date.today()
        start = today - timedelta(days=30 * months)

        hires = (
            db.query(
                func.date_trunc("month", Contrat.date_debut).label("month"),
                func.count(Contrat.id).label("count"),
            )
            .join(FicPersonne, FicPersonne.id == Contrat.fic_personne_id)
            .join(FicPersonneProjet, FicPersonne.id == FicPersonneProjet.fic_personne_id)
            .filter(
                FicPersonneProjet.acteur_id == acteur_id,
                Contrat.date_debut >= start,
            )
            .group_by(func.date_trunc("month", Contrat.date_debut))
            .order_by(func.date_trunc("month", Contrat.date_debut))
            .all()
        )

        return [
            {"mois": h.month.strftime("%b %y"), "nombre": h.count}
            for h in hires
            if h.month
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────
# 12. Couverture géographique vs objectifs
# ─────────────────────────────────────────────────────────────
@router.get("/couverture-geographique/{acteur_id}")
async def get_geographic_coverage(
    acteur_id: str, filter_type: str = "tous", db: Session = Depends(get_db)
):
    """Couverture géographique par région comparée aux objectifs."""
    try:
        today = date.today()

        OBJECTIFS = {
            "Abidjan": 25, "Bouaké": 12, "Yamoussoukro": 15,
            "Korhogo": 12, "San-Pédro": 8, "Daloa": 10,
            "Gagnoa": 10, "Duekoué": 8,
        }

        q = (
            db.query(TRegion.nom, func.count(FicPersonne.id.distinct()).label("effectif"))
            .join(FicPersonneLocalisation, TRegion.id == FicPersonneLocalisation.region_id)
            .join(Contrat, FicPersonneLocalisation.contrat_id == Contrat.id)
            .join(FicPersonne, Contrat.fic_personne_id == FicPersonne.id)
            .join(FicPersonneProjet, FicPersonne.id == FicPersonneProjet.fic_personne_id)
            .filter(FicPersonneProjet.acteur_id == acteur_id)
        )

        if filter_type == "actifs":
            q = q.filter(
                Contrat.date_debut <= today,
                or_(Contrat.date_fin >= today, Contrat.date_fin.is_(None))
            )
        elif filter_type == "inactifs":
            q = q.filter(Contrat.date_fin < today)

        results = q.group_by(TRegion.nom).all()

        coverage = []
        for region_nom, effectif in results:
            objectif = OBJECTIFS.get(region_nom, 10)
            taux = round(effectif * 100 / objectif) if objectif else 0
            deficit = max(0, objectif - effectif)
            intensite = "fort" if taux >= 100 else ("moyen" if taux >= 50 else "faible")
            coverage.append({
                "region": region_nom or "Non spécifiée",
                "effectif": effectif,
                "objectif": objectif,
                "couverture": taux,
                "deficit": deficit,
                "intensite": intensite,
            })

        return sorted(coverage, key=lambda x: x["couverture"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────
# 13. Top écoles
# ─────────────────────────────────────────────────────────────
@router.get("/top-ecoles/{acteur_id}")
async def get_top_schools(
    acteur_id: str, limit: int = 10, filter_type: str = "tous", db: Session = Depends(get_db)
):
    """Top N écoles / formations parmi les employés."""
    try:
        today = date.today()

        q = (
            db.query(Contrat.ecole, func.count(Contrat.id).label("count"))
            .join(FicPersonne, FicPersonne.id == Contrat.fic_personne_id)
            .join(FicPersonneProjet, FicPersonne.id == FicPersonneProjet.fic_personne_id)
            .filter(
                FicPersonneProjet.acteur_id == acteur_id,
                Contrat.ecole.isnot(None),
                Contrat.ecole != "-",
            )
        )

        if filter_type == "actifs":
            q = q.filter(
                Contrat.date_debut <= today,
                or_(Contrat.date_fin >= today, Contrat.date_fin.is_(None))
            )
        elif filter_type == "inactifs":
            q = q.filter(Contrat.date_fin < today)

        results = (
            q.group_by(Contrat.ecole)
            .order_by(func.count(Contrat.id).desc())
            .limit(limit)
            .all()
        )

        return [{"ecole": r[0], "nombre": r[1]} for r in results]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────
# 14. Statut des contrats (actifs / expirés / à venir)
# ─────────────────────────────────────────────────────────────
@router.get("/statut-contrats/{acteur_id}")
async def get_contract_status(acteur_id: str, db: Session = Depends(get_db)):
    """Répartition contrats actifs / expirés / à venir."""
    try:
        today = date.today()

        def _count(extra_filter):
            return (
                db.query(func.count(Contrat.id))
                .join(FicPersonne, FicPersonne.id == Contrat.fic_personne_id)
                .join(FicPersonneProjet, FicPersonne.id == FicPersonneProjet.fic_personne_id)
                .filter(FicPersonneProjet.acteur_id == acteur_id, extra_filter)
                .scalar() or 0
            )

        actifs   = _count(Contrat.date_debut <= today,)
        # recount with date_fin check
        actifs = (
            db.query(func.count(Contrat.id))
            .join(FicPersonne, FicPersonne.id == Contrat.fic_personne_id)
            .join(FicPersonneProjet, FicPersonne.id == FicPersonneProjet.fic_personne_id)
            .filter(
                FicPersonneProjet.acteur_id == acteur_id,
                Contrat.date_debut <= today,
                or_(Contrat.date_fin >= today, Contrat.date_fin.is_(None)),
            )
            .scalar() or 0
        )
        expires = (
            db.query(func.count(Contrat.id))
            .join(FicPersonne, FicPersonne.id == Contrat.fic_personne_id)
            .join(FicPersonneProjet, FicPersonne.id == FicPersonneProjet.fic_personne_id)
            .filter(
                FicPersonneProjet.acteur_id == acteur_id,
                Contrat.date_fin < today,
            )
            .scalar() or 0
        )
        a_venir = (
            db.query(func.count(Contrat.id))
            .join(FicPersonne, FicPersonne.id == Contrat.fic_personne_id)
            .join(FicPersonneProjet, FicPersonne.id == FicPersonneProjet.fic_personne_id)
            .filter(
                FicPersonneProjet.acteur_id == acteur_id,
                Contrat.date_debut > today,
            )
            .scalar() or 0
        )

        return {"actifs": actifs, "expires": expires, "aVenir": a_venir}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
