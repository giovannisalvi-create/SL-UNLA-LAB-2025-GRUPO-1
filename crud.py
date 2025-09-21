from sqlalchemy.orm import Session
from typing import List, Optional
import models, schemas

def create_persona(db: Session, persona_in: schemas.PersonaCreate) -> models.Persona:
    p = models.Persona(**persona_in.dict())
    db.add(p)
    db.commit()
    db.refresh(p)
    return p

def get_personas(db: Session, skip: int = 0, limit: int = 100) -> List[models.Persona]:
    return db.query(models.Persona).offset(skip).limit(limit).all()

def get_persona(db: Session, persona_id: int) -> Optional[models.Persona]:
    return db.query(models.Persona).filter(models.Persona.id == persona_id).first()


def update_persona(db: Session, persona_id: int, persona_up: schemas.PersonaUpdate) -> Optional[models.Persona]:
    p = get_persona(db, persona_id)
    if not p:
        return None
    for k, v in persona_up.dict(exclude_unset=True).items():
        setattr(p, k, v)
    db.add(p)
    db.commit()
    db.refresh(p)
    return p

def delete_persona(db: Session, persona_id: int) -> bool:
    p = get_persona(db, persona_id)
    if not p:
        return False
    db.delete(p)
    db.commit()
    return True

def create_turno(db: Session, turno_in: schemas.TurnoCreate) -> models.Turno:
    t = models.Turno(**turno_in.dict())
    db.add(t)
    db.commit()
    db.refresh(t)
    return t

def get_turnos(db: Session, skip: int = 0, limit: int = 100) -> List[models.Turno]:
    return db.query(models.Turno).offset(skip).limit(limit).all()

def get_turno(db: Session, turno_id: int) -> Optional[models.Turno]:
    return db.query(models.Turno).filter(models.Turno.id == turno_id).first()

def get_persona_por_dni(db: Session, dni: str) -> Optional[models.Persona]:
    return db.query(models.Persona).filter(models.Persona.dni == dni).first()