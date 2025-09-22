from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import Base, engine, get_db
import crud, schemas, models, services
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


@app.put("/personas/{persona_id}", response_model=schemas.PersonaOut)
def actualizar_persona(persona_id: int, persona_up: schemas.PersonaUpdate, db: Session = Depends(get_db)):
    db_persona = crud.get_persona(db, persona_id)
    if not db_persona:
        raise HTTPException(status_code=404, detail="Persona no encontrada")
    if persona_up.email and persona_up.email != db_persona.email and db.query(models.Persona).filter(models.Persona.email == persona_up.email).first():
        raise HTTPException(status_code=400, detail="Email ya registrado")
    if persona_up.dni and persona_up.dni != db_persona.dni and db.query(models.Persona).filter(models.Persona.dni == persona_up.dni).first():
        raise HTTPException(status_code=400, detail="DNI ya registrado")
    
    p = crud.update_persona(db, persona_id, persona_up)
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

@app.delete("/personas/{persona_id}")
def eliminar_persona(persona_id: int, db: Session = Depends(get_db)):
    ok = crud.delete_persona(db, persona_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Persona no encontrada")
    return {"ok": True, "mensaje": "Persona eliminada"}

@app.get("/turnos-disponibles")
def turnos_disponibles(fecha: str, db: Session = Depends(get_db)):
    from datetime import date
    try:
        fecha_obj = date.fromisoformat(fecha)
    except Exception:
        raise HTTPException(status_code=400, detail="Fecha inválida. Formato esperado: YYYY-MM-DD")
    disponibles = services.turnos_disponibles(db, fecha_obj)
    return {"fecha": fecha_obj, "horarios_disponibles": disponibles}

@app.post("/turnos", response_model=schemas.TurnoOut)
def crear_turno(turno: schemas.TurnoCreateConDNI, db: Session = Depends(get_db)):
    persona = crud.get_persona_por_dni(db, turno.dni)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona no encontrada")
    if not persona.habilitado:
        raise HTTPException(status_code=400, detail="Persona inhabilitada para sacar turno")
    if not services.puede_sacar_turno(db, persona.id):
        raise HTTPException(status_code=400, detail="La persona tiene 5 o más cancelados en los últimos 6 meses")
    
    turno_data = schemas.TurnoCreate(
        fecha=turno.fecha,
        hora=turno.hora,
        estado=turno.estado,
        persona_id=persona.id
    )
    t = crud.create_turno(db, turno_data)
    return schemas.TurnoOut(
        id=t.id,
        fecha=t.fecha,
        hora=t.hora,
        estado=t.estado,
        persona_id=t.persona_id,
        dni=persona.dni
    )

@app.get("/turnos", response_model=list[schemas.TurnoOut])
def listar_turnos(db: Session = Depends(get_db)):
    turnos = crud.get_turnos(db)
    out = []
    for t in turnos:
        persona = crud.get_persona(db, t.persona_id)
        out.append(schemas.TurnoOut(
            id=t.id,
            fecha=t.fecha,
            hora=t.hora,
            estado=t.estado,
            persona_id=t.persona_id,
            dni=persona.dni
        ))
    return out

@app.get("/turnos/{turno_id}", response_model=schemas.TurnoOut)
def obtener_turno(turno_id: int, db: Session = Depends(get_db)):
    t = crud.get_turno(db, turno_id)
    if not t:
        raise HTTPException(status_code=404, detail="Turno no encontrado")
    persona = crud.get_persona(db, t.persona_id)
    return schemas.TurnoOut(
        id=t.id,
        fecha=t.fecha,
        hora=t.hora,
        estado=t.estado,
        persona_id=t.persona_id,
        dni=persona.dni
    )