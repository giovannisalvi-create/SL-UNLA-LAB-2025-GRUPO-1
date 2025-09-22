from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import Base, engine, get_db
import crud, schemas
from datetime import date

Base.metadata.create_all(bind=engine)
app = FastAPI(title="TP - API de Turnos")

@app.get("/", include_in_schema=False)
def root():
    return {"mensaje": "API de turnos funcionando. Ir a /docs para la documentación."}

@app.post("/personas", response_model=schemas.PersonaOut)
def crear_persona(persona: schemas.PersonaCreate, db: Session = Depends(get_db)):
    if db.query(models.Persona).filter(models.Persona.email == persona.email).first():
        raise HTTPException(status_code=400, detail="Email ya registrado")
    if db.query(models.Persona).filter(models.Persona.dni == persona.dni).first():
        raise HTTPException(status_code=400, detail="DNI ya registrado")
    p = crud.create_persona(db, persona)
    today = date.today()
    edad = today.year - p.fecha_nacimiento.year - ((today.month, today.day) < (p.fecha_nacimiento.month, p.fecha_nacimiento.day))
    return schemas.PersonaOut(
        id=p.id,
        nombre=p.nombre,
        email=p.email,
        dni=p.dni,
        telefono=p.telefono,
        fecha_nacimiento=p.fecha_nacimiento,
        habilitado=p.habilitado,
        edad=edad
    )

@app.get("/personas", response_model=list[schemas.PersonaOut])
def listar_personas(db: Session = Depends(get_db)):
    personas = crud.get_personas(db)
    out = []
    for p in personas:
        today = date.today()
        edad = today.year - p.fecha_nacimiento.year - ((today.month, today.day) < (p.fecha_nacimiento.month, p.fecha_nacimiento.day))
        out.append(schemas.PersonaOut(
            id=p.id,
            nombre=p.nombre,
            email=p.email,
            dni=p.dni,
            telefono=p.telefono,
            fecha_nacimiento=p.fecha_nacimiento,
            habilitado=p.habilitado,
            edad=edad
        ))
    return out

@app.get("/personas/{persona_id}", response_model=schemas.PersonaOut)
def obtener_persona(persona_id: int, db: Session = Depends(get_db)):
    p = crud.get_persona(db, persona_id)
    if not p:
        raise HTTPException(status_code=404, detail="Persona no encontrada")
    today = date.today()
    edad = today.year - p.fecha_nacimiento.year - ((today.month, today.day) < (p.fecha_nacimiento.month, p.fecha_nacimiento.day))
    return schemas.PersonaOut(
        id=p.id,
        nombre=p.nombre,
        email=p.email,
        dni=p.dni,
        telefono=p.telefono,
        fecha_nacimiento=p.fecha_nacimiento,
        habilitado=p.habilitado,
        edad=edad
    )