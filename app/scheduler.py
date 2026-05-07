# -*- coding: utf-8 -*-
"""
Planificateur de tâches — AFOR Emploi
Rapport hebdomadaire envoyé chaque vendredi à 18h00 (heure locale)
"""

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


def _run_weekly_report():
    """Wrapper appelé par APScheduler — crée sa propre session DB."""
    try:
        from app.database import SessionLocal
        from app.email_service import send_weekly_reports
        db = SessionLocal()
        try:
            send_weekly_reports(db)
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Erreur rapport hebdomadaire: {e}", exc_info=True)


def start_scheduler():
    global _scheduler
    if _scheduler and _scheduler.running:
        return

    _scheduler = BackgroundScheduler(timezone="Africa/Abidjan")

    # Chaque vendredi à 18h00
    _scheduler.add_job(
        _run_weekly_report,
        trigger=CronTrigger(day_of_week="fri", hour=18, minute=0),
        id="weekly_report",
        name="Rapport hebdomadaire RESPO",
        replace_existing=True,
        misfire_grace_time=3600,  # tolère jusqu'à 1h de retard
    )

    _scheduler.start()
    logger.info("Scheduler démarré — rapport vendredi 18h00 (Africa/Abidjan)")


def stop_scheduler():
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler arrêté")
