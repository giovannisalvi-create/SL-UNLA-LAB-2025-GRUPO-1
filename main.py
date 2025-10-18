from fastapi import FastAPI, Depends, HTTPException ,Query
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
    persona_creada = crud.create_persona(db, persona)
    edad_calculada = services.calcular_edad(persona_creada.fecha_nacimiento)
    return schemas.PersonaOut(
        id=persona_creada.id,
        nombre=persona_creada.nombre,
        email=persona_creada.email,
        dni=persona_creada.dni,
        telefono=persona_creada.telefono,
        fecha_nacimiento=persona_creada.fecha_nacimiento,
        habilitado=persona_creada.habilitado,
        edad=edad_calculada
    )

@app.get("/personas", response_model=list[schemas.PersonaOut])
def listar_personas(db: Session = Depends(get_db)):
    personas = crud.get_personas(db)
    lista_de_personas = []
    for persona_db in personas:
        edad_calculada = services.calcular_edad(persona_db.fecha_nacimiento)
        lista_de_personas.append(schemas.PersonaOut(
            id=persona_db.id,
            nombre=persona_db.nombre,
            email=persona_db.email,
            dni=persona_db.dni,
            telefono=persona_db.telefono,
            fecha_nacimiento=persona_db.fecha_nacimiento,
            habilitado=persona_db.habilitado,
            edad=edad_calculada
        ))
    return lista_de_personas

@app.get("/personas/{persona_id}", response_model=schemas.PersonaOut)
def obtener_persona(persona_id: int, db: Session = Depends(get_db)):
    persona_obtenida = crud.get_persona(db, persona_id)
    if not persona_obtenida:
        raise HTTPException(status_code=404, detail="Persona no encontrada")
    edad_calculada = services.calcular_edad(persona_obtenida.fecha_nacimiento)
    return schemas.PersonaOut(
        id=persona_obtenida.id,
        nombre=persona_obtenida.nombre,
        email=persona_obtenida.email,
        dni=persona_obtenida.dni,
        telefono=persona_obtenida.telefono,
        fecha_nacimiento=persona_obtenida.fecha_nacimiento,
        habilitado=persona_obtenida.habilitado,
        edad=edad_calculada
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
    
    persona_actualizada = crud.update_persona(db, persona_id, persona_up)
    edad_calculada = services.calcular_edad(persona_actualizada.fecha_nacimiento) 
    return schemas.PersonaOut(
        id=persona_actualizada.id,
        nombre=persona_actualizada.nombre,
        email=persona_actualizada.email,
        dni=persona_actualizada.dni,
        telefono=persona_actualizada.telefono,
        fecha_nacimiento=persona_actualizada.fecha_nacimiento,
        habilitado=persona_actualizada.habilitado,
        edad=edad_calculada
    )

@app.delete("/personas/{persona_id}")
def eliminar_persona(persona_id: int, db: Session = Depends(get_db)):
    eliminacion_exitosa = crud.delete_persona(db, persona_id)
    if not eliminacion_exitosa:
        raise HTTPException(status_code=404, detail="Persona no encontrada")
    return {"ok": True, "mensaje": "Persona eliminada"}

@app.get("/turnos-disponibles")
def turnos_disponibles(fecha: str, db: Session = Depends(get_db)):
    #from datetime import date
    #Ya está el import al inicio del main
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
    turno_creado = crud.create_turno(db, turno_data)
    return schemas.TurnoOut(
        id=turno_creado.id,
        fecha=turno_creado.fecha,
        hora=turno_creado.hora,
        estado=turno_creado.estado,
        persona_id=turno_creado.persona_id,
        dni=persona.dni
    )

@app.get("/turnos", response_model=list[schemas.TurnoOut])
def listar_turnos(db: Session = Depends(get_db)):
    turnos_db = crud.get_turnos(db)
    lista_de_turnos = []
    for turno in turnos_db:
        persona = crud.get_persona(db, turno.persona_id)
        lista_de_turnos.append(schemas.TurnoOut(
            id=turno.id,
            fecha=turno.fecha,
            hora=turno.hora,
            estado=turno.estado,
            persona_id=turno.persona_id,
            dni=persona.dni
        ))
    return lista_de_turnos

@app.get("/turnos/{turno_id}", response_model=schemas.TurnoOut)
def obtener_turno(turno_id: int, db: Session = Depends(get_db)):
    turno_obtenido = crud.get_turno(db, turno_id)
    if not turno_obtenido:
        raise HTTPException(status_code=404, detail="Turno no encontrado")
    persona = crud.get_persona(db, turno_obtenido.persona_id)
    return schemas.TurnoOut(
        id=turno_obtenido.id,
        fecha=turno_obtenido.fecha,
        hora=turno_obtenido.hora,
        estado=turno_obtenido.estado,
        persona_id=turno_obtenido.persona_id,
        dni=persona.dni
    )

@app.put("/turnos/{turno_id}", response_model=schemas.TurnoOut)
def actualizar_turno(turno_id: int, turno_up: schemas.TurnoUpdate, db: Session = Depends(get_db)):
    turno_existente = crud.get_turno(db, turno_id)
    if not turno_existente:
        raise HTTPException(status_code=400, detail="Turno no encontrado")
    
    #Validar que el turno se puede modificar
    if not services.puede_modificar_turno(turno_existente):
        raise HTTPException(status_code=400, detail="No se puede modificar un turno asistido o cancelado")
    
    
    turno_actualizado = crud.update_turno(db, turno_id, turno_up)
    if not turno_actualizado:
        raise HTTPException(status_code=500, detail="Turno no encontrado")
    #t_con_persona = db.query(models.Turno).join(models.Persona).filter(models.Turno.id == turno_id).first()
    #Usamos turno_actualizado en lugar de hacer una nueva consulta.
    return schemas.TurnoOut(
        id=turno_actualizado.id,
        fecha=turno_actualizado.fecha,
        hora=turno_actualizado.hora,
        estado=turno_actualizado.estado,
        persona_id=turno_actualizado.persona_id,
        dni=turno_actualizado.persona.dni
    )

@app.put("/turnos/{turno_id}/cancelar", response_model=schemas.TurnoOut)
def cancelar_turno(turno_id: int, db: Session = Depends(get_db)):
    turno = crud.get_turno(db, turno_id)
    if not turno:
        raise HTTPException(status_code=404, detail="Turno no encontrado")

    if not services.puede_cancelar_turno(turno):
        raise HTTPException(status_code=400, detail="No se pueden cancelar turnos asistidos")

    if not services.puede_modificar_turno(turno):
        raise HTTPException(status_code=400, detail="No se puede cancelar un turno cancelado")
    
    #Actuliza solo el estado a cancelado (acá hacemos la eliminación lógica)
    turno_actualizado = crud.update_turno(db, turno_id, schemas.TurnoUpdate(estado="cancelado"))
    if not turno_actualizado:
        raise HTTPException(status_code=500, detail="Error al actualizar turno")
    
    persona = crud.get_persona(db, turno_actualizado.persona_id)
    return schemas.TurnoOut(
        id=turno_actualizado.id,
        fecha=turno_actualizado.fecha,
        hora=turno_actualizado.hora,
        estado=turno_actualizado.estado,
        persona_id=turno_actualizado.persona_id,
        dni=persona.dni
    )
    
@app.put("/turnos/{turno_id}/confirmar", response_model=schemas.TurnoOut)
def confirmar_turno(turno_id: int, db: Session = Depends(get_db)):
    turno = crud.get_turno(db, turno_id)
    if not turno:
        raise HTTPException(status_code=404, detail="Turno no encontrado")
    
    if not services.puede_modificar_turno(turno):
        raise HTTPException(status_code=400, detail="No se puede confirmar un turno asistido o cancelado")
    
    #Actualiza el estado solo a confirmado
    turno_actualizado = crud.update_turno(db, turno_id, schemas.TurnoUpdate(estado="confirmado"))
    
    if not turno_actualizado:
        raise HTTPException(status_code=500, detail="Error al actualizar el turno")
    
    persona = crud.get_persona(db, turno_actualizado.persona_id)
    return schemas.TurnoOut(
        id=turno_actualizado.id,
        fecha=turno_actualizado.fecha,
        hora=turno_actualizado.hora,
        estado=turno_actualizado.estado,
        persona_id=turno_actualizado.persona_id,
        dni=persona.dni
    )


@app.get("/reportes/turnos-por-fecha")
def turnos_por_fecha(fecha: date, db: Session = Depends(get_db)):
    turnos = crud.get_turnos_por_fecha(db, fecha)
    if not turnos:
        raise HTTPException(status_code=404, detail="No hay turnos para esa fecha")
    return [
        {
            "id": t.Turno.id,
            "fecha": t.Turno.fecha,
            "hora": t.Turno.hora,
            "estado": t.Turno.estado,
            "persona": {"nombre": t.nombre, "dni": t.dni},
        }
        for t in turnos
    ]


@app.get("/reportes/turnos-cancelados-por-mes")
def turnos_cancelados_por_mes(
    mes: int = Query(None, ge=1, le=12, description="Número del mes (1-12)"),
    anio: int = Query(None, ge=2022, le=2026, description="Año (ej. 2025)"),
    db: Session = Depends(get_db)
):
    hoy = date.today()
    mes = mes or hoy.month
    anio = anio or hoy.year

    turnos = crud.get_turnos_cancelados_por_mes(db, anio, mes)
    nombre_mes = services.nombre_mes(mes).capitalize()

    return {
        "anio": anio,
        "mes": nombre_mes,
        "cantidad": len(turnos),
        "turnos": [
            {
                "id": t.id,
                "persona_id": t.persona_id,
                "fecha": t.fecha,
                "hora": t.hora,
                "estado": t.estado,
            }
            for t in turnos
        ],
    }


@app.get("/reportes/turnos-por-persona")
def turnos_por_persona(dni: str, db: Session = Depends(get_db)):
    persona = crud.get_persona_por_dni(db, dni)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona no encontrada")

    turnos = crud.get_turnos_por_persona(db, persona.id)
    return {
        "persona": {"id": persona.id, "nombre": persona.nombre, "dni": persona.dni},
        "turnos": [
            {"id": t.id, "fecha": t.fecha, "hora": t.hora, "estado": t.estado}
            for t in turnos
        ],
    }

@app.get("/reportes/turnos-cancelados")
def reportes_turnos_cancelados(min: int = 5, db: Session = Depends(get_db)):
  
    turnos_cancelados = (
        db.query(models.Turno)
        .filter(models.Turno.estado == "cancelado")
        .all()
    )

    personas_dict = {}
    for turno in turnos_cancelados:
        persona = crud.get_persona(db, turno.persona_id)
        if not persona:
            continue
        if persona.id not in personas_dict:
            personas_dict[persona.id] = {
                "id": persona.id,
                "nombre": persona.nombre,
                "dni": persona.dni,
                "email": persona.email,
                "telefono": persona.telefono,
                "cantidad_cancelados": 0,
                "detalle_turnos_cancelados": []
            }
        personas_dict[persona.id]["cantidad_cancelados"] += 1
        personas_dict[persona.id]["detalle_turnos_cancelados"].append({
            "id": turno.id,
            "fecha": turno.fecha,
            "hora": turno.hora,
            "estado": turno.estado
        })

    resultado = [
        data for data in personas_dict.values()
        if data["cantidad_cancelados"] >= min
    ]

    return resultado


@app.get("/reportes/turnos-confirmados-periodos")
def reportes_turnos_confirmados_periodos(
    desde: str,
    hasta: str,
    pagina: int = 1,
    por_pagina: int = 5,
    db: Session = Depends(get_db)
):

    # Validar formato de fechas
    try:
        fecha_desde = date.fromisoformat(desde)
        fecha_hasta = date.fromisoformat(hasta)
    except Exception:
        raise HTTPException(status_code=400, detail="Formato de fecha inválido. Use YYYY-MM-DD.")

    # Obtener lista de turnos confirmados usando services.py
    try:
        turnos_confirmados = services.obtener_turnos_confirmados_periodos(db, fecha_desde, fecha_hasta)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Paginación
    total = len(turnos_confirmados)
    total_paginas = (total + por_pagina - 1) // por_pagina
    inicio = (pagina - 1) * por_pagina
    fin = inicio + por_pagina
    turnos_pagina = turnos_confirmados[inicio:fin]

   
    resultados = []
    for turno in turnos_pagina:
        persona = crud.get_persona(db, turno.persona_id)
        resultados.append({
            "id": turno.id,
            "fecha": turno.fecha,
            "hora": turno.hora,
            "estado": turno.estado,
            "persona": {
                "id": persona.id,
                "nombre": persona.nombre,
                "dni": persona.dni,
                "email": persona.email
            }
        })

    return {
        "total": total,
        "pagina_actual": pagina,
        "por_pagina": por_pagina,
        "total_paginas": total_paginas,
        "resultados": resultados
    }

@app.get("/reportes/estado-personas")
def reporte_estado_personas(db: Session = Depends(get_db)):
    personas = crud.get_personas(db)
    resultado = []

    for persona in personas:
        
        puede_sacar = services.puede_sacar_turno(db, persona.id)
        estado = "habilitado" if persona.habilitado and puede_sacar else "inhabilitado"

        resultado.append({
            "id": persona.id,
            "nombre": persona.nombre,
            "dni": persona.dni,
            "email": persona.email,
            "telefono": persona.telefono,
            "habilitado": persona.habilitado,
            "puede_sacar_turno": puede_sacar,
            "estado_general": estado
        })

    return resultado