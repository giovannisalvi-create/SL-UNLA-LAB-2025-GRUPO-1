from sqlalchemy.orm import Session
from datetime import date, timedelta
from typing import List
import models
from config import settings

def calcular_edad(fecha_nacimiento: date) -> int:
    today = date.today()
    return today.year - fecha_nacimiento.year - ((today.month, today.day) < (fecha_nacimiento.month, fecha_nacimiento.day))

def puede_sacar_turno(db: Session, persona_id: int) -> bool:
    seis_meses = date.today() - timedelta(days=182)
    cancelados = db.query(models.Turno).filter(
        models.Turno.persona_id == persona_id,
        #models.Turno.estado == "cancelado",
        models.Turno.estado == settings.ESTADO_CANCELADO,
        models.Turno.fecha >= seis_meses,
    ).count()
    return cancelados < 5

def turnos_disponibles(db: Session, fecha: date) -> List[str]:
    #horarios_totales = [f"{h:02d}:{m:02d}" for h in range(9, 17) for m in (0, 30)]
    horarios_totales = settings.HORARIOS_VALIDOS.copy()
    
    ocupados_rows = db.query(models.Turno.hora).filter(
        models.Turno.fecha == fecha,
        models.Turno.estado != "cancelado",
    ).all()
    
    ocupados = [r[0] for r in ocupados_rows]
    disponibles = [h for h in horarios_totales if h not in ocupados]
    return disponibles 

def validar_estado_modificable(turno: models.Turno) -> str:
    
    # if turno.estado in ["asistido", "cancelado"]:
    #     return turno.estado
    if turno.estado == settings.ESTADO_ASISTIDO:
        return settings.ESTADO_ASISTIDO
    
    if turno.estado == settings.ESTADO_CANCELADO:
        return settings.ESTADO_CANCELADO
    
    return None

def obtener_turnos_confirmados_periodos(db, desde: date, hasta: date):
    if desde > hasta:
        raise ValueError("La fecha inicial no puede ser posterior a la final")

    turnos_confirmados = (
        db.query(models.Turno)
        .filter(
            #models.Turno.estado == "confirmado",
            models.Turno.estado == settings.ESTADO_CONFIRMADO,
            models.Turno.fecha >= desde,
            models.Turno.fecha <= hasta
        )
        #offset limit/size
        .order_by(models.Turno.fecha)
        .all()
    )

    return turnos_confirmados

def nombre_mes(mes: int) -> str:
    MESES = {
        1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
        5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
        9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"
    }
    return MESES.get(mes, "mes desconocido")
