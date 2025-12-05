from sqlalchemy.orm import Session
from typing import List, Optional
import models, schemas
from datetime import date
from sqlalchemy import func

def create_persona(db: Session, persona_in: schemas.PersonaCreate) -> models.Persona:
    persona_db = models.Persona(**persona_in.model_dump())
    db.add(persona_db)
    db.commit()
    db.refresh(persona_db)
    return persona_db

def get_personas(db: Session, skip: int = 0, limit: int = 100) -> List[models.Persona]:
    return db.query(models.Persona).offset(skip).limit(limit).all()

def get_persona(db: Session, persona_id: int) -> Optional[models.Persona]:
    return db.query(models.Persona).filter(models.Persona.id == persona_id).first()


def update_persona(db: Session, persona_id: int, persona_up: schemas.PersonaUpdate) -> Optional[models.Persona]:
    persona_db = get_persona(db, persona_id)
    if not persona_db:
        return None
    for campo, valor in persona_up.model_dump(exclude_unset=True).items():
        setattr(persona_db, campo, valor)
    db.add(persona_db)
    db.commit()
    db.refresh(persona_db)
    return persona_db

def delete_persona(db: Session, persona_id: int) -> bool:
    persona_a_eliminar = get_persona(db, persona_id)
    if not persona_a_eliminar:
        return False
    db.delete(persona_a_eliminar)
    db.commit()
    return True

def create_turno(db: Session, turno_in: schemas.TurnoCreate) -> models.Turno:
    turno_db = models.Turno(**turno_in.model_dump())
    db.add(turno_db)
    db.commit()
    db.refresh(turno_db)
    return turno_db

def get_turnos(db: Session, skip: int = 0, limit: int = 100) -> List[models.Turno]:
    return db.query(models.Turno).offset(skip).limit(limit).all()

def get_turno(db: Session, turno_id: int) -> Optional[models.Turno]:
    return db.query(models.Turno).filter(models.Turno.id == turno_id).first()

def get_persona_por_dni(db: Session, dni: str) -> Optional[models.Persona]:
    return db.query(models.Persona).filter(models.Persona.dni == dni).first()

def update_turno(db: Session, turno_id: int, turno_up: schemas.TurnoUpdate) -> Optional[models.Turno]:
    turno_db = get_turno(db, turno_id)
    if not turno_db:
        return None
    for campo, valor in turno_up.model_dump(exclude_unset=True).items():
        setattr(turno_db, campo, valor)
    db.add(turno_db)
    db.commit()
    db.refresh(turno_db)
    return turno_db

def delete_turno(db: Session, turno_id: int) -> bool:
    turno_a_eliminar = get_turno(db, turno_id)
    if not turno_a_eliminar:
        return False
    db.delete(turno_a_eliminar)
    db.commit()
    return 

def get_turnos_por_fecha(db: Session, fecha: date):
    return (
        db.query(models.Turno, models.Persona.nombre, models.Persona.dni)
        .join(models.Persona, models.Turno.persona_id == models.Persona.id)
        .filter(models.Turno.fecha == fecha)
        .all()
    )

def get_turnos_cancelados_por_mes(db: Session, anio: int, mes: int):
    return (
        db.query(models.Turno)
        .filter(
            func.strftime("%Y", models.Turno.fecha) == str(anio),
            func.strftime("%m", models.Turno.fecha) == f"{mes:02d}",
            models.Turno.estado == "cancelado",
        )
        .all()
    )

    
def get_persona_por_dni(db: Session, dni: str):
    return db.query(models.Persona).filter(models.Persona.dni == dni).first()

def get_turnos_por_persona(db: Session, persona_id: int, skip: int = 0, limit: int = 10):
    return (
        db.query(models.Turno)
        .filter(models.Turno.persona_id == persona_id)
        .order_by(models.Turno.fecha, models.Turno.hora)
        .offset(skip)
        .limit(limit)
        .all()
    )



