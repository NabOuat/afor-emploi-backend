# 📋 Mapping des champs - Création d'employé

## Frontend → Backend → Base de données

### 🔵 Informations personnelles (fic_personne)

| Champ Frontend | Valeur envoyée (clé backend) | Colonne BD | Table | Notes |
|----------------|------------------------------|------------|-------|-------|
| `formData.matricule` | `matricule` | `matricule` | `fic_personne` | ✅ Correct |
| `formData.nom` | `nom` | `nom` | `fic_personne` | ✅ Correct |
| `formData.prenom` | `prenom` | `prenom` | `fic_personne` | ✅ Correct |
| `formData.genre` | `genre` | `genre` | `fic_personne` | ✅ Correct |
| `formData.dateNaissance` | `date_naissance` | `date_naissance` | `fic_personne` | ✅ Correct |
| `formData.contact` | `contact` | `contact` | `fic_personne` | ✅ Correct |

---

### 🟢 Informations de contrat (contrat)

| Champ Frontend | Valeur envoyée (clé backend) | Colonne BD | Table | Notes |
|----------------|------------------------------|------------|-------|-------|
| `formData.statutProfessionnel` | `type_personne` | `type_personne` | `contrat` | ✅ Correct (Contractuel/Fonctionnaire) |
| `formData.diplome` | `diplome` | `diplome` | `contrat` | ✅ Correct |
| `formData.ecole` | `ecole` | `ecole` | `contrat` | ✅ Correct (converti en ARRAY) |
| `formData.dateDebut` | `date_debut` | `date_debut` | `contrat` | ✅ Correct |
| `formData.dateFin` | `date_fin` | `date_fin` | `contrat` | ✅ Correct |
| `formData.poste` | `poste_nom` | `poste_nom` | `contrat` | ✅ Correct (ex: Assistant, Chauffeur) |
| `formData.categorie` | `categorie_poste` | `categorie_poste` | `contrat` | ✅ Correct (ex: Cadre, Agent) |
| `formData.qualification` | `poste` | `poste` | `contrat` | ⚠️ **ATTENTION: Confusion de nommage** |
| `formData.natureContrat` | `type_contrat` | `type_contrat` | `contrat` | ✅ Correct (CDI, CDD, Stage) |

---

### 🟡 Localisation (fic_personne_localisation)

| Champ Frontend | Valeur envoyée (clé backend) | Colonne BD | Table | Notes |
|----------------|------------------------------|------------|-------|-------|
| `formData.region` | `region_id` | `region_id` | `fic_personne_localisation` | ✅ Correct |
| `formData.departement` | `departement_id` | `departement_id` | `fic_personne_localisation` | ✅ Correct |
| `formData.sousPrefecture` | `sous_prefecture_id` | `sous_prefecture_id` | `fic_personne_localisation` | ✅ Correct |

---

### 🔴 Projets (fic_personne_projet)

| Champ Frontend | Valeur envoyée (clé backend) | Colonne BD | Table | Notes |
|----------------|------------------------------|------------|-------|-------|
| `selectedProjets[]` | `projets[].projet_id` | `projet_id` | `fic_personne_projet` | ✅ Correct |
| - | - | `fic_personne_id` | `fic_personne_projet` | ✅ Auto-généré |
| - | - | `acteur_id` | `fic_personne_projet` | ✅ Depuis URL param |

---

## 🔍 Problèmes identifiés

### ❌ Problème 1: Confusion `poste` vs `qualification`

**Dans le frontend:**
- `formData.poste` → Envoyé comme `poste_nom` (ex: "Assistant", "Chauffeur")
- `formData.qualification` → Envoyé comme `poste` (ex: "DUT", "Ingénieur")

**Dans la BD:**
- `contrat.poste_nom` = Nom du poste (ex: "Assistant")
- `contrat.poste` = Qualification/Fonction (ex: "DUT", "Ingénieur")

**Impact:** Les valeurs sont inversées ou mal affichées

---

### ❌ Problème 2: École affichée comme "Inconnu"

**Cause possible:**
- Le champ `ecole` est de type `ARRAY` dans la BD
- L'affichage récupère `ecole[0]` mais peut-être mal géré

---

### ❌ Problème 3: Localisation affichée comme "-"

**Cause possible:**
- Les IDs sont stockés mais les noms ne sont pas récupérés via JOIN
- Besoin de vérifier la requête de récupération des employés

---

## 🛠️ Actions recommandées

1. ✅ Vérifier le mapping `poste` vs `qualification` dans CreateEmployeeModal
2. ✅ Vérifier l'affichage de `ecole` (ARRAY → String)
3. ✅ Vérifier les JOINs pour récupérer les noms de région/département/sous-préfecture
4. ✅ Ajouter des logs console dans le backend pour tracer les valeurs reçues

---

## 📝 Exemple de payload envoyé

```json
{
  "nom": "ANEY",
  "prenom": "NANA",
  "date_naissance": "1995-02-03",
  "genre": "M",
  "contact": "0123456789",
  "matricule": null,
  "diplome": "DUT",
  "type_personne": "Contractuel",
  "poste_nom": "Assistant",
  "categorie_poste": "Cadre",
  "type_contrat": "CDI",
  "poste": "DUT",  // ⚠️ Devrait être la qualification, pas le diplôme
  "ecole": "Institut XYZ",
  "date_debut": "2024-07-01",
  "date_fin": null,
  "region_id": null,
  "departement_id": null,
  "sous_prefecture_id": null,
  "projets": [{"projet_id": "xxx"}]
}
```

---

**Date de création:** 2026-02-03  
**Dernière mise à jour:** 2026-02-03
