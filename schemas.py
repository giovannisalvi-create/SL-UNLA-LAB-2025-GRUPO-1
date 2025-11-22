from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, Literal
from datetime import date, datetime

EstadoLiteral = Literal["pendiente", "cancelado", "confirmado", "asistido"]

def validar_logica_horario_turno(hora_str: str) -> str:
    #Validamos formato y convertimos a objeto 'time'
    try:
        hora_convertida = datetime.strptime(hora_str, "%H:%M").time()
    except ValueError:
        raise ValueError("Formato de hora inválido. Use HH:MM (ej: 14:30)")
    
    hora_numero = hora_convertida.hour
    minutos_numero = hora_convertida.minute

    if minutos_numero not in (0, 30):
        raise ValueError("Los turnos deben ser en intervalos de 30 minutos (ej: 09:00, 09:30)")
    
    if hora_numero < 9 or hora_numero > 16:
        raise ValueError("Los turnos están disponibles de 09:00 a 16:30")
    
    # Si la hora es 16, el último turno permitido es 16:30
    if hora_numero == 16 and minutos_numero > 30:
        raise ValueError("El último turno disponible es a las 16:30")
    
    return hora_str


def validar_hora_requerida(hora_ingresada: str) -> str:
    # Aunque Pydantic ya verifica si es 'str', esta capa añade el manejo de errores
    if not isinstance(hora_ingresada, str) or not hora_ingresada.strip():
        raise ValueError("La hora es un campo requerido y no puede estar vacío.")
        
    return validar_logica_horario_turno(hora_ingresada)

def validar_hora_opcional(hora_ingresada: Optional[str]) -> Optional[str]:
    if hora_ingresada is None:
        return None

    return validar_logica_horario_turno(hora_ingresada)

#abm de personas

class PersonaBase(BaseModel):
    nombre: str
    email: EmailStr
    dni: str
    telefono: Optional[str]
    fecha_nacimiento: date
    habilitado: Optional[bool] = True

class PersonaCreate(PersonaBase):
    pass

class PersonaOut(PersonaBase):
    id: int
    edad: int

    class Config:
        from_attributes = True

class PersonaUpdate(BaseModel):
    nombre: Optional[str] = None
    email: Optional[EmailStr] = None
    dni: Optional[str] = None
    telefono: Optional[str] = None
    fecha_nacimiento: Optional[date] = None
    habilitado: Optional[bool] = None

#----------------------
#abm de turnos
#----------------------

class TurnoBase(BaseModel):
    fecha: date
    hora: str
    estado: Optional[EstadoLiteral] = "pendiente"

    @field_validator("hora")
    @classmethod
    def validar_hora_turno(cls, v: str) -> str:
        return validar_logica_horario_turno(v)
    # @field_validator("hora")
    # def validar_formato_hora(cls, v):
    #     try:
    #         datetime.strptime(v, "%H:%M")
    #     except Exception:
    #         raise ValueError("Hora invalida. Formato esperado: HH:MM")
    #     return v

class TurnoCreateConDNI(BaseModel):
    fecha: date
    hora: str
    estado: Optional[EstadoLiteral] = "pendiente"
    dni: str

    @field_validator("hora")
    @classmethod
    def validar_hora_turno(cls, v: str) -> str:
        # Mismo método, misma llamada a la lógica central
        return validar_logica_horario_turno(v)
    #validar_hora = validar_hora_turno
    # @field_validator("hora")
    # def validar_formato_hora(cls, v):
    #     try:
    #         datetime.strptime(v, "%H:%M")
    #     except Exception:
    #         raise ValueError("Hora invalida. Formato esperado: HH:MM")
    #     return v

class TurnoCreate(TurnoBase):
    persona_id: int


class TurnoUpdate(BaseModel):
    fecha: Optional[date] = None
    hora: Optional[str] = None
    estado: Optional[EstadoLiteral] = None
    persona_id: Optional[int] = None

    @field_validator("hora")
    @classmethod
    def validar_hora_turno_opcional(cls, v: Optional[str]) -> Optional[str]:
        # Si no se envía (es None), se permite
        if v is None:
            return None
        # Si se envía (es un string), se valida la lógica central
        return validar_logica_horario_turno(v)
    #validar_hora = validar_hora_turno
    # @field_validator("hora")
    # def validar_formato_hora_opcional(cls, v):
    #     if v is None:
    #         return v
    #     try:
    #         datetime.strptime(v, "%H:%M")
    #     except Exception:
    #         raise ValueError("Hora invalida. Formato esperado: HH:MM")
    #     return v
    
class TurnoOut(TurnoBase):
    id: int
    persona_id: int
    dni: str

    class Config:
        from_attributes = True

PersonaOut.model_rebuild()