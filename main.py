from fastapi import FastAPI
from database import Base, engine

Base.metadata.create_all(bind=engine)
app = FastAPI(title="TP - API de Turnos")

@app.get("/", include_in_schema=False)
def root():
    return {"mensaje": "API de turnos funcionando. Ir a /docs para la documentación."}

@app.put("/turnos/{turno_id}", response_model=schemas.TurnoOut)
def actualizar_turno(turno_id: int, turno_up: schemas.TurnoUpdate, db: Session = Depends(get_db)):
    t = crud.update_turno(db, turno_id, turno_up)
    if not t:
        raise HTTPException(status_code=404, detail="Turno no encontrado")
    t_con_persona = db.query(models.Turno).join(models.Persona).filter(models.Turno.id == turno_id).first()
    return schemas.TurnoOut(
        id=t_con_persona.id,
        fecha=t_con_persona.fecha,
        hora=t_con_persona.hora,
        estado=t_con_persona.estado,
        persona_id=t_con_persona.persona_id,
        dni=t_con_persona.persona.dni
    )

@app.delete("/turnos/{turno_id}")
def eliminar_turno(turno_id: int, db: Session = Depends(get_db)):
    ok = crud.delete_turno(db, turno_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Turno no encontrado")
    return {"ok": True, "mensaje": "Turno eliminado"}