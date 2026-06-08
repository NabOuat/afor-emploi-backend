#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour vérifier que les statistiques du dashboard sont correctes
"""

import psycopg2
from dotenv import load_dotenv
import os
from datetime import date

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:Nabaga@localhost:5432/emploi?client_encoding=utf8')

def verify_stats():
    """Vérifier les statistiques"""
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        print("🔍 Vérification des Statistiques du Dashboard")
        print("=" * 70)
        
        # Récupérer un acteur_id pour tester
        cur.execute("SELECT id, nom FROM acteur WHERE type_acteur = 'OF' LIMIT 1")
        acteur = cur.fetchone()
        
        if not acteur:
            print("❌ Aucun acteur OF trouvé")
            return
        
        acteur_id, acteur_nom = acteur
        print(f"\n📊 Vérification pour l'acteur: {acteur_nom} (ID: {acteur_id})")
        print("-" * 70)
        
        # 1. Total employés
        cur.execute("""
            SELECT COUNT(*) FROM fic_personne 
            WHERE acteur_id = %s
        """, (acteur_id,))
        total_employees = cur.fetchone()[0]
        print(f"\n1️⃣  Total Employés: {total_employees}")
        
        # 2. Contrats actifs
        today = date.today()
        cur.execute("""
            SELECT COUNT(DISTINCT fp.id) FROM fic_personne fp
            JOIN contrat c ON fp.id = c.fic_personne_id
            WHERE fp.acteur_id = %s
            AND c.date_debut <= %s
            AND (c.date_fin >= %s OR c.date_fin IS NULL)
        """, (acteur_id, today, today))
        active_contracts = cur.fetchone()[0]
        print(f"2️⃣  Contrats Actifs: {active_contracts}")
        
        # 3. Contrats terminés
        cur.execute("""
            SELECT COUNT(DISTINCT fp.id) FROM fic_personne fp
            JOIN contrat c ON fp.id = c.fic_personne_id
            WHERE fp.acteur_id = %s
            AND c.date_fin < %s
        """, (acteur_id, today))
        completed_contracts = cur.fetchone()[0]
        print(f"3️⃣  Contrats Terminés: {completed_contracts}")
        
        # 4. Jeunes > 25 ans
        cur.execute("""
            SELECT COUNT(*) FROM fic_personne 
            WHERE acteur_id = %s
            AND date_naissance IS NOT NULL
            AND EXTRACT(YEAR FROM AGE(CURRENT_DATE, date_naissance)) > 25
        """, (acteur_id,))
        young_employees = cur.fetchone()[0]
        print(f"4️⃣  Jeunes > 25 ans: {young_employees}")
        
        # 5. Durée moyenne des contrats
        cur.execute("""
            SELECT AVG((COALESCE(c.date_fin, CURRENT_DATE)::date - c.date_debut::date))
            FROM fic_personne fp
            JOIN contrat c ON fp.id = c.fic_personne_id
            WHERE fp.acteur_id = %s
            AND c.date_debut IS NOT NULL
        """, (acteur_id,))
        result = cur.fetchone()[0]
        avg_duration_days = int(result) if result else 0
        avg_duration_months = int(avg_duration_days / 30) if avg_duration_days else 0
        print(f"5️⃣  Durée Moyenne Contrats: {avg_duration_months} mois ({avg_duration_days} jours)")
        
        # 6. Répartition par projet
        print(f"\n6️⃣  Répartition par Projet:")
        cur.execute("""
            SELECT p.nom, COUNT(fp.id) as count
            FROM fic_personne fp
            JOIN projet p ON fp.projet_id = p.projet_id
            WHERE fp.acteur_id = %s
            GROUP BY p.projet_id, p.nom
            ORDER BY count DESC
        """, (acteur_id,))
        projects = cur.fetchall()
        if projects:
            for proj_name, count in projects:
                print(f"   - {proj_name}: {count}")
        else:
            print("   ⚠️  Aucun projet trouvé")
        
        # 7. Répartition par genre
        print(f"\n7️⃣  Répartition par Genre:")
        cur.execute("""
            SELECT COALESCE(genre, 'Non spécifié') as genre, COUNT(*) as count
            FROM fic_personne
            WHERE acteur_id = %s
            GROUP BY genre
            ORDER BY count DESC
        """, (acteur_id,))
        genders = cur.fetchall()
        total_gender = sum([g[1] for g in genders])
        for gender, count in genders:
            percentage = (count / total_gender * 100) if total_gender > 0 else 0
            print(f"   - {gender}: {count} ({percentage:.1f}%)")
        
        # 8. Statistiques d'âge
        print(f"\n8️⃣  Statistiques d'Âge:")
        cur.execute("""
            SELECT 
                AVG(EXTRACT(YEAR FROM AGE(CURRENT_DATE, date_naissance)))::INT as avg_age,
                MIN(EXTRACT(YEAR FROM AGE(CURRENT_DATE, date_naissance)))::INT as min_age,
                MAX(EXTRACT(YEAR FROM AGE(CURRENT_DATE, date_naissance)))::INT as max_age
            FROM fic_personne
            WHERE acteur_id = %s
            AND date_naissance IS NOT NULL
        """, (acteur_id,))
        age_stats = cur.fetchone()
        if age_stats[0]:
            print(f"   - Âge Moyen: {age_stats[0]} ans")
            print(f"   - Âge Min: {age_stats[1]} ans")
            print(f"   - Âge Max: {age_stats[2]} ans")
        
        # 9. Répartition par zone
        print(f"\n9️⃣  Répartition par Zone:")
        cur.execute("""
            SELECT DISTINCT 
                COALESCE(r.nom, 'N/A') as region,
                COALESCE(d.nom, 'N/A') as departement,
                COUNT(DISTINCT fpl.id) as count
            FROM fic_personne_localisation fpl
            JOIN contrat c ON fpl.contrat_id = c.id
            JOIN fic_personne fp ON c.fic_personne_id = fp.id
            LEFT JOIN tregion r ON fpl.region_id = r.id
            LEFT JOIN tdepartement d ON fpl.departement_id = d.id
            WHERE fp.acteur_id = %s
            GROUP BY r.id, d.id, r.nom, d.nom
            ORDER BY count DESC
        """, (acteur_id,))
        zones = cur.fetchall()
        if zones:
            for region, dept, count in zones:
                print(f"   - {region} / {dept}: {count}")
        else:
            print("   ⚠️  Aucune zone trouvée")
        
        # 10. Répartition par poste (top 5)
        print(f"\n🔟 Top 5 Postes:")
        cur.execute("""
            SELECT c.poste_nom, COUNT(fp.id) as count
            FROM fic_personne fp
            JOIN contrat c ON fp.id = c.fic_personne_id
            WHERE fp.acteur_id = %s
            GROUP BY c.poste_nom
            ORDER BY count DESC
            LIMIT 5
        """, (acteur_id,))
        positions = cur.fetchall()
        for pos_name, count in positions:
            print(f"   - {pos_name}: {count}")
        
        print("\n" + "=" * 70)
        print("✅ Vérification terminée!")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")

if __name__ == "__main__":
    verify_stats()
