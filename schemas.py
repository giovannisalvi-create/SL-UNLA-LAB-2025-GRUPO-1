from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, Literal
from datetime import date, datetime

EstadoLiteral = Literal["pendiente", "cancelado", "confirmado", "asistido"]

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
    def validar_formato_hora(cls, v):
        try:
            datetime.strptime(v, "%H:%M")
        except Exception:
            raise ValueError("Hora invalida. Formato esperado: HH:MM")
        return v

class TurnoCreateConDNI(BaseModel):
    fecha: date
    hora: str
    estado: Optional[EstadoLiteral] = "pendiente"
    dni: str

    @field_validator("hora")
    def validar_formato_hora(cls, v):
        try:
            datetime.strptime(v, "%H:%M")
        except Exception:
            raise ValueError("Hora invalida. Formato esperado: HH:MM")
        return v

class TurnoCreate(TurnoBase):
    persona_id: int


class TurnoUpdate(BaseModel):
    fecha: Optional[date] = None
    hora: Optional[str] = None
    estado: Optional[EstadoLiteral] = None
    persona_id: Optional[int] = None

    @field_validator("hora")
    def validar_formato_hora_opcional(cls, v):
        if v is None:
            return v
        try:
            datetime.strptime(v, "%H:%M")
        except Exception:
            raise ValueError("Hora invalida. Formato esperado: HH:MM")
        return v
    
class TurnoOut(TurnoBase):
    id: int
    persona_id: int
    dni: str

    class Config:
        from_attributes = True

PersonaOut.model_rebuild()