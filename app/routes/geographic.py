from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import TRegion, TDepartement, TSousPrefecture
from app.schemas import TRegion as TRegionSchema, TRegionCreate, TDepartement as TDepartementSchema, TDepartementCreate, TSousPrefecture as TSousPrefectureSchema, TSousPrefectureCreate
import uuid

router = APIRouter(prefix="/api/geographic", tags=["geographic"])

# ============================================
# REGION ENDPOINTS
# ============================================

@router.get("/regions", response_model=List[TRegionSchema])
async def get_regions(db: Session = Depends(get_db)):
    return db.query(TRegion).all()

@router.get("/regions/{region_id}", response_model=TRegionSchema)
async def get_region(region_id: str, db: Session = Depends(get_db)):
    region = db.query(TRegion).filter(TRegion.id == region_id).first()
    if not region:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Region not found")
    return region

@router.post("/regions", response_model=TRegionSchema)
async def create_region(region: TRegionCreate, db: Session = Depends(get_db)):
    db_region = TRegion(id=region.id, nom=region.nom)
    db.add(db_region)
    db.commit()
    db.refresh(db_region)
    return db_region

@router.put("/regions/{region_id}", response_model=TRegionSchema)
async def update_region(region_id: str, region: TRegionCreate, db: Session = Depends(get_db)):
    db_region = db.query(TRegion).filter(TRegion.id == region_id).first()
    if not db_region:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Region not found")
    db_region.nom = region.nom
    db.commit()
    db.refresh(db_region)
    return db_region

@router.delete("/regions/{region_id}")
async def delete_region(region_id: str, db: Session = Depends(get_db)):
    db_region = db.query(TRegion).filter(TRegion.id == region_id).first()
    if not db_region:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Region not found")
    db.delete(db_region)
    db.commit()
    return {"message": "Region deleted"}

# ============================================
# DEPARTEMENT ENDPOINTS
# ============================================

@router.get("/departements", response_model=List[TDepartementSchema])
async def get_departements(region_id: str = None, db: Session = Depends(get_db)):
    query = db.query(TDepartement)
    if region_id:
        query = query.filter(TDepartement.region_id == region_id)
    return query.all()

@router.get("/departements/{departement_id}", response_model=TDepartementSchema)
async def get_departement(departement_id: str, db: Session = Depends(get_db)):
    departement = db.query(TDepartement).filter(TDepartement.id == departement_id).first()
    if not departement:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Departement not found")
    return departement

@router.post("/departements", response_model=TDepartementSchema)
async def create_departement(departement: TDepartementCreate, db: Session = Depends(get_db)):
    region = db.query(TRegion).filter(TRegion.id == departement.region_id).first()
    if not region:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Region not found")
    
    db_departement = TDepartement(
        id=departement.id,
        nom=departement.nom,
        region_id=departement.region_id
    )
    db.add(db_departement)
    db.commit()
    db.refresh(db_departement)
    return db_departement

@router.put("/departements/{departement_id}", response_model=TDepartementSchema)
async def update_departement(departement_id: str, departement: TDepartementCreate, db: Session = Depends(get_db)):
    db_departement = db.query(TDepartement).filter(TDepartement.id == departement_id).first()
    if not db_departement:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Departement not found")
    
    region = db.query(TRegion).filter(TRegion.id == departement.region_id).first()
    if not region:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Region not found")
    
    db_departement.nom = departement.nom
    db_departement.region_id = departement.region_id
    db.commit()
    db.refresh(db_departement)
    return db_departement

@router.delete("/departements/{departement_id}")
async def delete_departement(departement_id: str, db: Session = Depends(get_db)):
    db_departement = db.query(TDepartement).filter(TDepartement.id == departement_id).first()
    if not db_departement:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Departement not found")
    db.delete(db_departement)
    db.commit()
    return {"message": "Departement deleted"}

# ============================================
# SOUS-PREFECTURE ENDPOINTS
# ============================================

@router.get("/sousprefectures", response_model=List[TSousPrefectureSchema])
async def get_sousprefectures(departement_id: str = None, db: Session = Depends(get_db)):
    query = db.query(TSousPrefecture)
    if departement_id:
        query = query.filter(TSousPrefecture.departement_id == departement_id)
    return query.all()

@router.get("/sousprefectures/{sousprefecture_id}", response_model=TSousPrefectureSchema)
async def get_sousprefecture(sousprefecture_id: str, db: Session = Depends(get_db)):
    sousprefecture = db.query(TSousPrefecture).filter(TSousPrefecture.id == sousprefecture_id).first()
    if not sousprefecture:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sous-prefecture not found")
    return sousprefecture

@router.post("/sousprefectures", response_model=TSousPrefectureSchema)
async def create_sousprefecture(sousprefecture: TSousPrefectureCreate, db: Session = Depends(get_db)):
    departement = db.query(TDepartement).filter(TDepartement.id == sousprefecture.departement_id).first()
    if not departement:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Departement not found")
    
    db_sousprefecture = TSousPrefecture(
        id=sousprefecture.id,
        nom=sousprefecture.nom,
        departement_id=sousprefecture.departement_id
    )
    db.add(db_sousprefecture)
    db.commit()
    db.refresh(db_sousprefecture)
    return db_sousprefecture

@router.put("/sousprefectures/{sousprefecture_id}", response_model=TSousPrefectureSchema)
async def update_sousprefecture(sousprefecture_id: str, sousprefecture: TSousPrefectureCreate, db: Session = Depends(get_db)):
    db_sousprefecture = db.query(TSousPrefecture).filter(TSousPrefecture.id == sousprefecture_id).first()
    if not db_sousprefecture:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sous-prefecture not found")
    
    departement = db.query(TDepartement).filter(TDepartement.id == sousprefecture.departement_id).first()
    if not departement:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Departement not found")
    
    db_sousprefecture.nom = sousprefecture.nom
    db_sousprefecture.departement_id = sousprefecture.departement_id
    db.commit()
    db.refresh(db_sousprefecture)
    return db_sousprefecture

@router.delete("/sousprefectures/{sousprefecture_id}")
async def delete_sousprefecture(sousprefecture_id: str, db: Session = Depends(get_db)):
    db_sousprefecture = db.query(TSousPrefecture).filter(TSousPrefecture.id == sousprefecture_id).first()
    if not db_sousprefecture:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sous-prefecture not found")
    db.delete(db_sousprefecture)
    db.commit()
    return {"message": "Sous-prefecture deleted"}
