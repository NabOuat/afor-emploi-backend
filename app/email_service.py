# -*- coding: utf-8 -*-
"""
Service d'envoi d'emails — AFOR Emploi
Rapport hebdomadaire automatique pour les Responsables (vendredi 18h00)
"""

import smtplib
import logging
from datetime import date, datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.config import settings

logger = logging.getLogger(__name__)


# ─── Calcul des statistiques OF+AF ─────────────────────────────────────────
def compute_weekly_stats(db: Session) -> dict:
    try:
        result = db.execute(text("""
            SELECT
                fp.id,
                fp.genre,
                fp.date_naissance,
                c.type_contrat,
                c.type_personne,
                c.date_debut,
                c.date_fin,
                c.diplome,
                r.nom  AS region,
                a.nom  AS acteur_nom,
                a.type_acteur,
                p.nom  AS projet_nom,
                CASE
                    WHEN c.date_debut IS NOT NULL
                         AND c.date_debut <= CURRENT_DATE
                         AND (c.date_fin IS NULL OR c.date_fin >= CURRENT_DATE)
                    THEN TRUE ELSE FALSE
                END AS is_active
            FROM fic_personne_projet fpp
            INNER JOIN fic_personne fp  ON fpp.fic_personne_id = fp.id
            INNER JOIN acteur a          ON fpp.acteur_id       = a.id
            LEFT  JOIN contrat c         ON c.fic_personne_id   = fp.id
            LEFT  JOIN fic_personne_localisation l ON l.contrat_id = c.id
            LEFT  JOIN tregion r         ON r.id                = l.region_id
            LEFT  JOIN projet p          ON p.id                = fpp.projet_id
            WHERE a.type_acteur IN ('OF', 'AF')
            ORDER BY fp.id, c.date_debut DESC
        """))
        rows = result.fetchall()
    except Exception as e:
        logger.error(f"Erreur compute_weekly_stats: {e}", exc_info=True)
        return {}

    seen_ids = set()
    employees = []
    today = date.today()

    for row in rows:
        emp_id = row[0]
        if emp_id in seen_ids:
            continue
        seen_ids.add(emp_id)

        dob = row[2]
        age = 0
        if dob:
            try:
                age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            except Exception:
                age = 0

        date_fin = row[6]
        is_active = bool(row[12])

        employees.append({
            "id": emp_id,
            "genre": row[1] or "M",
            "age": age,
            "type_contrat": row[3] or "—",
            "type_personne": row[4] or "—",
            "date_debut": row[5],
            "date_fin": date_fin,
            "diplome": row[7] or "Non spécifié",
            "region": row[8] or "N/A",
            "acteur_nom": row[9] or "—",
            "type_acteur": row[10] or "—",
            "projet_nom": row[11] or "—",
            "is_active": is_active,
        })

    total  = len(employees)
    if total == 0:
        return {"total": 0}

    cdi        = sum(1 for e in employees if e["type_contrat"] == "CDI")
    cdd        = sum(1 for e in employees if e["type_contrat"] == "CDD")
    consultant = sum(1 for e in employees if e["type_contrat"] == "Consultant")
    hommes     = sum(1 for e in employees if e["genre"] == "M")
    femmes     = sum(1 for e in employees if e["genre"] == "F")
    actifs     = sum(1 for e in employees if e["is_active"])
    expires    = total - actifs

    ages = [e["age"] for e in employees if e["age"] > 0]
    age_moyen = round(sum(ages) / len(ages)) if ages else 0

    # Régions top 5
    region_map: dict[str, int] = {}
    for e in employees:
        r = e["region"]
        region_map[r] = region_map.get(r, 0) + 1
    top_regions = sorted(region_map.items(), key=lambda x: x[1], reverse=True)[:5]

    # Acteurs top 5
    acteur_map: dict[str, int] = {}
    for e in employees:
        a = f"[{e['type_acteur']}] {e['acteur_nom']}"
        acteur_map[a] = acteur_map.get(a, 0) + 1
    top_acteurs = sorted(acteur_map.items(), key=lambda x: x[1], reverse=True)[:5]

    # Contrats à échéance
    d3  = today + timedelta(days=90)
    d6  = today + timedelta(days=180)
    d12 = today + timedelta(days=365)
    exp_3  = sum(1 for e in employees if e["date_fin"] and today < e["date_fin"] <= d3  and e["is_active"])
    exp_6  = sum(1 for e in employees if e["date_fin"] and d3  < e["date_fin"] <= d6  and e["is_active"])
    exp_12 = sum(1 for e in employees if e["date_fin"] and d6  < e["date_fin"] <= d12 and e["is_active"])

    # Embauches ce mois-ci et la semaine passée
    lun = today - timedelta(days=today.weekday() + 7)
    ven = lun + timedelta(days=4)
    this_month_start = today.replace(day=1)
    new_week  = sum(1 for e in employees if e["date_debut"] and lun <= e["date_debut"] <= ven)
    new_month = sum(1 for e in employees if e["date_debut"] and e["date_debut"] >= this_month_start)

    # Niveaux d'éducation top 4
    educ_map: dict[str, int] = {}
    for e in employees:
        d = e["diplome"]
        educ_map[d] = educ_map.get(d, 0) + 1
    top_educ = sorted(educ_map.items(), key=lambda x: x[1], reverse=True)[:4]

    return {
        "total": total,
        "cdi": cdi, "cdd": cdd, "consultant": consultant,
        "hommes": hommes, "femmes": femmes,
        "taux_fem": round(femmes * 100 / total) if total else 0,
        "actifs": actifs, "expires": expires,
        "taux_activation": round(actifs * 100 / total) if total else 0,
        "age_moyen": age_moyen,
        "age_min": min(ages) if ages else 0,
        "age_max": max(ages) if ages else 0,
        "top_regions": top_regions,
        "top_acteurs": top_acteurs,
        "exp_3": exp_3, "exp_6": exp_6, "exp_12": exp_12,
        "new_week": new_week, "new_month": new_month,
        "top_educ": top_educ,
        "ratio_perm_temp": f"{cdi}/{cdd + consultant}",
    }


# ─── Template email formel (texte sobre) ────────────────────────────────────
def build_email_html(respo_name: str, stats: dict) -> str:
    if not stats or stats.get("total", 0) == 0:
        return "<p>Aucune donnée disponible cette semaine.</p>"

    s = stats
    now = datetime.now()
    week_num = now.isocalendar()[1]
    date_str = now.strftime("%d %B %Y")

    def pct(n):
        t = s["total"]
        return f"{round(n * 100 / t)} %" if t else "0 %"

    def tbl_row(label, value, alt=False):
        bg = "#f7f7f7" if alt else "#ffffff"
        return (f'<tr style="background:{bg};">'
                f'<td style="padding:7px 12px;border:1px solid #ddd;font-size:13px;color:#222;">{label}</td>'
                f'<td style="padding:7px 12px;border:1px solid #ddd;font-size:13px;color:#222;text-align:right;font-weight:600;">{value}</td>'
                f'</tr>')

    # Régions
    reg_rows = "".join(
        tbl_row(reg, f"{cnt} ({pct(cnt)})", i % 2 != 0)
        for i, (reg, cnt) in enumerate(s["top_regions"])
    )
    # Acteurs
    act_rows = "".join(
        tbl_row(act, f"{cnt} ({pct(cnt)})", i % 2 != 0)
        for i, (act, cnt) in enumerate(s["top_acteurs"])
    )
    # Éducation
    educ_rows = "".join(
        tbl_row(dip or "Non renseigné", f"{cnt} ({pct(cnt)})", i % 2 != 0)
        for i, (dip, cnt) in enumerate(s["top_educ"])
    )

    def section(title):
        return (f'<p style="margin:22px 0 4px;font-size:13px;font-weight:700;'
                f'color:#222;text-transform:uppercase;letter-spacing:.5px;'
                f'border-bottom:1px solid #aaa;padding-bottom:4px;">{title}</p>')

    def simple_table(header_left, header_right, rows_html):
        return (f'<table width="100%" cellpadding="0" cellspacing="0" '
                f'style="border-collapse:collapse;margin-top:6px;font-family:Arial,sans-serif;">'
                f'<tr style="background:#222;">'
                f'<th style="padding:7px 12px;border:1px solid #222;font-size:12px;color:#fff;text-align:left;">{header_left}</th>'
                f'<th style="padding:7px 12px;border:1px solid #222;font-size:12px;color:#fff;text-align:right;">{header_right}</th>'
                f'</tr>{rows_html}</table>')

    exp_warning = ""
    if s["exp_3"] > 0:
        exp_warning = (f'<p style="margin:6px 0 0;font-size:12px;color:#555;font-style:italic;">'
                       f'Attention : {s["exp_3"]} contrat(s) arrivent à échéance dans moins de 3 mois. '
                       f'Il est recommandé d\'engager les démarches de renouvellement sans délai.</p>')

    return f"""<!DOCTYPE html>
<html lang="fr">
<head><meta charset="UTF-8">
<title>Rapport Hebdomadaire AFOR Emploi — Semaine {week_num}</title></head>
<body style="margin:0;padding:0;background:#ffffff;font-family:Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#ffffff;">
<tr><td style="max-width:640px;margin:0 auto;display:block;padding:40px 48px;">

  <!-- En-tête -->
  <p style="margin:0 0 4px;font-size:11px;color:#555;text-align:right;">{date_str}</p>
  <p style="margin:0 0 28px;font-size:11px;color:#555;text-align:right;">Semaine {week_num} / {now.year}</p>

  <p style="margin:0 0 6px;font-size:13px;color:#222;"><strong>AFOR Emploi</strong> — Système de gestion des employés</p>
  <p style="margin:0 0 28px;font-size:13px;color:#222;">À l'attention de : <strong>{respo_name}</strong></p>

  <p style="margin:0 0 28px;font-size:14px;font-weight:700;color:#222;text-align:center;
     text-transform:uppercase;letter-spacing:1px;border-top:2px solid #222;
     border-bottom:2px solid #222;padding:10px 0;">
    Rapport hebdomadaire — Situation des employés OF / AF
  </p>

  <!-- Intro -->
  <p style="margin:0 0 16px;font-size:13px;color:#333;line-height:1.7;">
    Madame, Monsieur,
  </p>
  <p style="margin:0 0 24px;font-size:13px;color:#333;line-height:1.7;">
    J'ai l'honneur de vous soumettre, ci-après, le compte rendu hebdomadaire
    relatif à la situation des employés relevant des acteurs de type
    <strong>Organisme de Formation (OF)</strong> et
    <strong>Acteur de Formation (AF)</strong>,
    arrêtée au <strong>{date_str}</strong>.
  </p>

  <!-- I. Effectif global -->
  {section("I. Effectif global")}
  {simple_table("Indicateur", "Valeur",
    tbl_row("Effectif total (OF + AF)", s['total']) +
    tbl_row("Contrats actifs", f"{s['actifs']} ({pct(s['actifs'])})", True) +
    tbl_row("Contrats expirés", f"{s['expires']} ({pct(s['expires'])})", False) +
    tbl_row("Embauches — semaine écoulée", s['new_week'], True) +
    tbl_row("Embauches — mois en cours", s['new_month'], False)
  )}

  <!-- II. Répartition par type de contrat -->
  {section("II. Répartition par type de contrat")}
  {simple_table("Type de contrat", "Effectif",
    tbl_row("CDI (Contrat à Durée Indéterminée)", f"{s['cdi']} ({pct(s['cdi'])})") +
    tbl_row("CDD (Contrat à Durée Déterminée)", f"{s['cdd']} ({pct(s['cdd'])})", True) +
    tbl_row("Consultant / Prestataire", f"{s['consultant']} ({pct(s['consultant'])})", False)
  )}

  <!-- III. Répartition par genre -->
  {section("III. Répartition par genre et données démographiques")}
  {simple_table("Indicateur", "Valeur",
    tbl_row("Hommes", f"{s['hommes']} ({pct(s['hommes'])})") +
    tbl_row("Femmes", f"{s['femmes']} ({pct(s['femmes'])})", True) +
    tbl_row("Taux de féminisation", f"{s['taux_fem']} %", False) +
    tbl_row("Âge moyen", f"{s['age_moyen']} ans", True) +
    tbl_row("Âge minimum / maximum", f"{s['age_min']} ans / {s['age_max']} ans", False)
  )}

  <!-- IV. Échéances de contrats -->
  {section("IV. Contrats arrivant à échéance")}
  {simple_table("Horizon", "Nombre de contrats",
    tbl_row("Moins de 3 mois (urgent)", s['exp_3']) +
    tbl_row("3 à 6 mois", s['exp_6'], True) +
    tbl_row("6 à 12 mois", s['exp_12'], False)
  )}
  {exp_warning}

  <!-- V. Répartition régionale -->
  {section("V. Répartition par région (Top 5)")}
  {simple_table("Région", "Effectif"  , reg_rows)}

  <!-- VI. Top acteurs -->
  {section("VI. Principaux acteurs OF / AF")}
  {simple_table("Acteur", "Effectif", act_rows)}

  <!-- VII. Niveau d'éducation -->
  {section("VII. Niveau de formation (Top 4)")}
  {simple_table("Diplôme / Niveau", "Effectif", educ_rows)}

  <!-- Conclusion -->
  <p style="margin:32px 0 8px;font-size:13px;color:#333;line-height:1.7;">
    Ce rapport a été généré automatiquement par le système
    <strong>AFOR Emploi</strong> chaque vendredi à 18h00 (heure d'Abidjan).
    Pour toute question ou rectification, veuillez contacter le service
    d'administration du système.
  </p>

  <p style="margin:24px 0 4px;font-size:13px;color:#333;line-height:1.7;">
    Veuillez agréer, Madame, Monsieur, l'expression de notre considération distinguée.
  </p>

  <p style="margin:28px 0 0;font-size:13px;color:#222;font-weight:700;">Respectueusement,</p>
  <p style="margin:4px 0 0;font-size:13px;color:#333;">Le Système AFOR Emploi</p>
  <p style="margin:2px 0 0;font-size:12px;color:#777;">Rapport automatique — Ne pas répondre à cet email</p>

</td></tr>
</table>
</body></html>"""


# ─── Envoi SMTP ─────────────────────────────────────────────────────────────
def send_email(to_email: str, to_name: str, subject: str, html_body: str) -> bool:
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.warning("SMTP non configuré — email non envoyé")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = Header(subject, "utf-8")
        msg["From"]    = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
        msg["To"]      = f"{to_name} <{to_email}>"

        msg.attach(MIMEText(html_body, "html", "utf-8"))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_FROM_EMAIL, [to_email], msg.as_string())

        logger.info(f"Email envoyé à {to_email}")
        return True

    except Exception as e:
        logger.error(f"Erreur envoi email à {to_email}: {e}", exc_info=True)
        return False


# ─── Job principal : envoi à tous les RESPO ──────────────────────────────────
def send_weekly_reports(db: Session):
    logger.info("Démarrage du rapport hebdomadaire AFOR Emploi…")

    try:
        from app.models import Users, Acteur
        respos = (
            db.query(Users)
            .join(Acteur, Acteur.id == Users.acteur_id)
            .filter(Acteur.type_acteur == "RESPO")
            .filter(Users.email.isnot(None))
            .filter(Users.email != "")
            .all()
        )
    except Exception as e:
        logger.error(f"Erreur récupération RESPO: {e}", exc_info=True)
        return

    if not respos:
        logger.info("Aucun responsable avec un email configuré.")
        return

    stats = compute_weekly_stats(db)
    now   = datetime.now()
    week  = now.isocalendar()[1]
    subject = f"[AFOR Emploi] Rapport hebdomadaire — Semaine {week} / {now.year}"

    sent = 0
    for user in respos:
        name = f"{user.prenom or ''} {user.nom or ''}".strip() or user.username
        html = build_email_html(name, stats)
        if send_email(user.email, name, subject, html):
            sent += 1

    logger.info(f"Rapports envoyés : {sent}/{len(respos)}")
