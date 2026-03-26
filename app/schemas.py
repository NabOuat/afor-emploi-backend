from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import date, datetime

# ============================================
# GEOGRAPHIC SCHEMAS
# ============================================

class TRegionBase(BaseModel):
    id: str
    nom: str

class TRegionCreate(TRegionBase):
    pass

class TRegion(TRegionBase):
    class Config:
        from_attributes = True


class TDepartementBase(BaseModel):
    id: str
    nom: str
    region_id: str

class TDepartementCreate(TDepartementBase):
    pass

class TDepartement(TDepartementBase):
    class Config:
        from_attributes = True


class TSousPrefectureBase(BaseModel):
    id: str
    nom: str
    departement_id: str

class TSousPrefectureCreate(TSousPrefectureBase):
    pass

class TSousPrefecture(TSousPrefectureBase):
    class Config:
        from_attributes = True


# ============================================
# AUTHENTICATION SCHEMAS
# ============================================

class UsersBase(BaseModel):
    username: str

class UsersCreate(UsersBase):
    password: str
    acteur_id: str

class Users(UsersBase):
    id: str
    acteur_id: str
    class Config:
        from_attributes = True


class AdministrateurBase(BaseModel):
    nom: str
    prenom: str
    email: Optional[str] = None
    contact: Optional[str] = None
    role: Optional[str] = None

class AdministrateurCreate(AdministrateurBase):
    user_id: str

class Administrateur(AdministrateurBase):
    id: str
    user_id: str
    date_creation: datetime
    class Config:
        from_attributes = True


# ============================================
# ACTOR SCHEMAS
# ============================================

class ActeurBase(BaseModel):
    nom: str
    type_acteur: str
    contact_1: Optional[str] = None
    contact_2: Optional[str] = None
    adresse_1: Optional[str] = None
    adresse_2: Optional[str] = None
    email_1: Optional[str] = None
    email_2: Optional[str] = None

class ActeurCreate(ActeurBase):
    pass

class Acteur(ActeurBase):
    id: str
    date_creation: datetime
    class Config:
        from_attributes = True


# ============================================
# PROJECT SCHEMAS
# ============================================

class ProjetBase(BaseModel):
    nom: str
    nom_complet: Optional[str] = None

class ProjetCreate(ProjetBase):
    pass

class Projet(ProjetBase):
    id: str
    class Config:
        from_attributes = True


# ============================================
# INTERVENTION ZONE SCHEMAS
# ============================================

class ZoneDInterventionBase(BaseModel):
    acteur_id: str
    projet_id: str
    region_id: Optional[str] = None
    departement_id: Optional[str] = None
    sous_prefecture_id: Optional[str] = None

class ZoneDInterventionCreate(ZoneDInterventionBase):
    pass

class ZoneDIntervention(ZoneDInterventionBase):
    id: str
    class Config:
        from_attributes = True


# ============================================
# PERSON & CONTRACT SCHEMAS
# ============================================

class SupervisionBase(BaseModel):
    superviseur_id: Optional[str] = None
    date_debut: Optional[date] = None
    date_fin: Optional[date] = None

class SupervisionCreate(SupervisionBase):
    fic_personne_id: str

class Supervision(SupervisionBase):
    id: str
    fic_personne_id: str
    class Config:
        from_attributes = True


class ContratBase(BaseModel):
    poste_nom: str
    categorie_poste: Optional[str] = None
    type_contrat: Optional[str] = None
    type_personne: Optional[str] = None
    poste: Optional[str] = None
    date_debut: date
    date_fin: Optional[date] = None
    diplome: Optional[str] = None
    ecole: Optional[str] = None

class ContratCreate(ContratBase):
    fic_personne_id: str

class Contrat(ContratBase):
    id: str
    fic_personne_id: str
    class Config:
        from_attributes = True


class FicPersonneLocalisationBase(BaseModel):
    region_id: Optional[str] = None
    departement_id: Optional[str] = None
    sous_prefecture_id: Optional[str] = None
    date_debut: Optional[date] = None

class FicPersonneLocalisationCreate(FicPersonneLocalisationBase):
    contrat_id: str

class FicPersonneLocalisation(FicPersonneLocalisationBase):
    id: str
    contrat_id: str
    class Config:
        from_attributes = True


class FicPersonneBase(BaseModel):
    nom: str
    prenom: str
    date_naissance: Optional[date] = None
    genre: Optional[str] = None
    contact: Optional[str] = None
    matricule: Optional[str] = None

class FicPersonneCreate(FicPersonneBase):
    pass

class FicPersonne(FicPersonneBase):
    id: str
    class Config:
        from_attributes = True


# ============================================
# AUTH SCHEMAS
# ============================================

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    actor_type: str
    username: str
    acteur_id: str

class LoginRequest(BaseModel):
    username: str
    password: str


# ============================================
# USER ACTIONS SCHEMAS
# ============================================

class UserActionCreate(BaseModel):
    user_id: str
    username: str
    acteur_id: str
    action_type: str
    action_description: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None


class UserActionResponse(BaseModel):
    id: str
    user_id: str
    username: str
    acteur_id: str
    action_type: str
    action_description: Optional[str]
    resource_type: Optional[str]
    resource_id: Optional[str]
    ip_address: Optional[str]
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True
