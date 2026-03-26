from sqlalchemy import Column, String, Integer, Date, Boolean, ForeignKey, Text, DateTime, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

# ============================================
# GEOGRAPHIC HIERARCHY MODELS
# ============================================

class TRegion(Base):
    __tablename__ = "tregion"
    
    id = Column(String, primary_key=True)
    nom = Column(String, nullable=False)
    
    departements = relationship("TDepartement", back_populates="region", cascade="all, delete-orphan")
    zones_intervention = relationship("ZoneDIntervention", back_populates="region")
    localisations = relationship("FicPersonneLocalisation", back_populates="region")


class TDepartement(Base):
    __tablename__ = "tdepartement"
    
    id = Column(String, primary_key=True)
    nom = Column(String, nullable=False)
    region_id = Column(String, ForeignKey("tregion.id", ondelete="CASCADE"), nullable=False)
    
    region = relationship("TRegion", back_populates="departements")
    sousprefectures = relationship("TSousPrefecture", back_populates="departement", cascade="all, delete-orphan")
    localisations = relationship("FicPersonneLocalisation", back_populates="departement")


class TSousPrefecture(Base):
    __tablename__ = "tsousprefecture"
    
    id = Column(String, primary_key=True)
    nom = Column(String, nullable=False)
    departement_id = Column(String, ForeignKey("tdepartement.id", ondelete="CASCADE"), nullable=False)
    
    departement = relationship("TDepartement", back_populates="sousprefectures")
    localisations = relationship("FicPersonneLocalisation", back_populates="sous_prefecture")


# ============================================
# ACTOR & AUTHENTICATION MODELS
# ============================================

class Acteur(Base):
    __tablename__ = "acteur"
    
    id = Column(String, primary_key=True)
    nom = Column(String, nullable=False)
    type_acteur = Column(String, nullable=False)
    contact_1 = Column(String)
    contact_2 = Column(String)
    adresse_1 = Column(String)
    adresse_2 = Column(String)
    email_1 = Column(String)
    email_2 = Column(String)
    date_creation = Column(DateTime, default=datetime.utcnow)
    
    users = relationship("Users", back_populates="acteur", cascade="all, delete-orphan")
    zones_intervention = relationship("ZoneDIntervention", back_populates="acteur", cascade="all, delete-orphan")
    fic_personne_projets = relationship("FicPersonneProjet", back_populates="acteur", cascade="all, delete-orphan")
    actions = relationship("UserAction", back_populates="acteur", cascade="all, delete-orphan")


class Users(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)
    username = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    nom = Column(String, nullable=True)
    prenom = Column(String, nullable=True)
    acteur_id = Column(String, ForeignKey("acteur.id", ondelete="CASCADE"), nullable=False)
    
    acteur = relationship("Acteur", back_populates="users")
    administrateur = relationship("Administrateur", back_populates="user", uselist=False, cascade="all, delete-orphan")
    actions = relationship("UserAction", back_populates="user", cascade="all, delete-orphan")


class Administrateur(Base):
    __tablename__ = "administrateur"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    nom = Column(String, nullable=False)
    prenom = Column(String, nullable=False)
    email = Column(String)
    contact = Column(String)
    role = Column(String)
    date_creation = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("Users", back_populates="administrateur")


# ============================================
# PROJECT & INTERVENTION ZONE MODELS
# ============================================

class Projet(Base):
    __tablename__ = "projet"
    
    id = Column(String, primary_key=True)
    nom = Column(String, nullable=False)
    nom_complet = Column(String)
    
    zones_intervention = relationship("ZoneDIntervention", back_populates="projet", cascade="all, delete-orphan")
    fic_personnes = relationship("FicPersonneProjet", back_populates="projet", cascade="all, delete-orphan")
    engagements = relationship("ProjetEngagement", back_populates="projet", cascade="all, delete-orphan")


class Engagement(Base):
    __tablename__ = "engagement"
    
    id = Column(String, primary_key=True)
    nom = Column(String, nullable=False, unique=True)
    description = Column(Text)
    date_creation = Column(DateTime, default=datetime.utcnow)
    
    projets = relationship("ProjetEngagement", back_populates="engagement", cascade="all, delete-orphan")
    contrats = relationship("Contrat", back_populates="engagement")


class ProjetEngagement(Base):
    __tablename__ = "projet_engagement"
    
    id = Column(String, primary_key=True)
    projet_id = Column(String, ForeignKey("projet.id", ondelete="CASCADE"), nullable=False)
    engagement_id = Column(String, ForeignKey("engagement.id", ondelete="CASCADE"), nullable=False)
    date_creation = Column(DateTime, default=datetime.utcnow)
    
    projet = relationship("Projet", back_populates="engagements")
    engagement = relationship("Engagement", back_populates="projets")


class ZoneDIntervention(Base):
    __tablename__ = "zone_d_intervention"
    
    id = Column(String, primary_key=True)
    acteur_id = Column(String, ForeignKey("acteur.id", ondelete="CASCADE"), nullable=False)
    projet_id = Column(String, ForeignKey("projet.id", ondelete="CASCADE"), nullable=False)
    region_id = Column(String, ForeignKey("tregion.id", ondelete="SET NULL"))
    
    acteur = relationship("Acteur", back_populates="zones_intervention")
    projet = relationship("Projet", back_populates="zones_intervention")
    region = relationship("TRegion", back_populates="zones_intervention")


# ============================================
# PERSON & CONTRACT MODELS
# ============================================

class FicPersonneProjet(Base):
    __tablename__ = "fic_personne_projet"
    
    id = Column(String, primary_key=True)
    fic_personne_id = Column(String, ForeignKey("fic_personne.id", ondelete="CASCADE"), nullable=False)
    projet_id = Column(String, ForeignKey("projet.id", ondelete="CASCADE"), nullable=False)
    acteur_id = Column(String, ForeignKey("acteur.id", ondelete="CASCADE"), nullable=False)
    
    fic_personne = relationship("FicPersonne", back_populates="projets")
    projet = relationship("Projet", back_populates="fic_personnes")
    acteur = relationship("Acteur", back_populates="fic_personne_projets")


class FicPersonne(Base):
    __tablename__ = "fic_personne"
    
    id = Column(String, primary_key=True)
    nom = Column(String, nullable=False)
    prenom = Column(String, nullable=False)
    date_naissance = Column(Date)
    genre = Column(String)
    contact = Column(String)
    matricule = Column(String, unique=True)
    created_by = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    projets = relationship("FicPersonneProjet", back_populates="fic_personne", cascade="all, delete-orphan")
    supervision = relationship("Supervision", back_populates="fic_personne", uselist=False, cascade="all, delete-orphan")
    contrat = relationship("Contrat", back_populates="fic_personne", uselist=False, cascade="all, delete-orphan", foreign_keys="Contrat.fic_personne_id")
    creator = relationship("Users", foreign_keys=[created_by])


class Supervision(Base):
    __tablename__ = "supervision"
    
    id = Column(String, primary_key=True)
    fic_personne_id = Column(String, ForeignKey("fic_personne.id", ondelete="CASCADE"), nullable=False)
    superviseur_id = Column(String)
    date_debut = Column(Date)
    date_fin = Column(Date)
    
    fic_personne = relationship("FicPersonne", back_populates="supervision")


class Contrat(Base):
    __tablename__ = "contrat"
    
    id = Column(String, primary_key=True)
    fic_personne_id = Column(String, ForeignKey("fic_personne.id", ondelete="CASCADE"), nullable=False)
    projet_id = Column(String, ForeignKey("projet.id", ondelete="SET NULL"))
    engagement_id = Column(String, ForeignKey("engagement.id", ondelete="SET NULL"))
    poste_nom = Column(String, nullable=False)
    categorie_poste = Column(String)
    type_contrat = Column(String)
    type_personne = Column(String)
    poste = Column(String)
    date_debut = Column(Date, nullable=False)
    date_fin = Column(Date)
    diplome = Column(String)
    ecole = Column(String)
    
    fic_personne = relationship("FicPersonne", back_populates="contrat")
    projet = relationship("Projet")
    engagement = relationship("Engagement", back_populates="contrats")
    localisations = relationship("FicPersonneLocalisation", back_populates="contrat", cascade="all, delete-orphan")


class FicPersonneLocalisation(Base):
    __tablename__ = "fic_personne_localisation"
    
    id = Column(String, primary_key=True)
    contrat_id = Column(String, ForeignKey("contrat.id", ondelete="CASCADE"), nullable=False)
    region_id = Column(String, ForeignKey("tregion.id", ondelete="SET NULL"))
    departement_id = Column(String, ForeignKey("tdepartement.id", ondelete="SET NULL"))
    sous_prefecture_id = Column(String, ForeignKey("tsousprefecture.id", ondelete="SET NULL"))
    date_debut = Column(Date)
    
    contrat = relationship("Contrat", back_populates="localisations")
    region = relationship("TRegion", back_populates="localisations")
    departement = relationship("TDepartement", back_populates="localisations")
    sous_prefecture = relationship("TSousPrefecture", back_populates="localisations")


# ============================================
# USER ACTIONS TRACKING MODEL
# ============================================

class UserAction(Base):
    __tablename__ = "user_actions"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    username = Column(String, nullable=False)
    acteur_id = Column(String, ForeignKey("acteur.id", ondelete="CASCADE"), nullable=False)
    action_type = Column(String, nullable=False)
    action_description = Column(String)
    resource_type = Column(String)
    resource_id = Column(String)
    ip_address = Column(String)
    user_agent = Column(String)
    status = Column(String, default="success")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("Users", back_populates="actions")
    acteur = relationship("Acteur", back_populates="actions")
