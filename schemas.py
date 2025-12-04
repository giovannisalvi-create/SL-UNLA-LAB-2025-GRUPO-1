from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import date
from config import settings

def validar_existencia_horaria(hora_str: str) -> str:
    """Valida que la hora exista en la lista generada por config"""
    if hora_str not in settings.HORARIOS_VALIDOS:
        raise ValueError(
            f"Horario inválido. Los turnos son de {settings.INICIO} a {settings.FIN} "
            f"cada {settings.INTERVALO} minutos. Ejemplos: {settings.HORARIOS_VALIDOS[:3]}..."
        )
    return hora_str

# ----------------------
# ABM de Personas
# ----------------------

class PersonaBase(BaseModel):
    nombre: str
    email: EmailStr
    dni: str
    telefono: Optional[str] = None
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

# ----------------------
# ABM de Turnos
# ----------------------

class TurnoBase(BaseModel):
    fecha: date
    hora: str
    estado: Optional[str] = settings.ESTADO_PENDIENTE

    @field_validator("hora")
    @classmethod
    def validar_hora_turno(cls, v: str) -> str:
        return validar_existencia_horaria(v)
    
    @field_validator("estado")
    @classmethod
    def validar_estado(cls, v: Optional[str]) -> Optional[str]:
        if v and v not in settings.ESTADOS_VALIDOS:
            raise ValueError(f"Estado inválido. Permitidos: {settings.ESTADOS_VALIDOS}")
        return v

class TurnoCreateConDNI(BaseModel):
    fecha: date
    hora: str
    estado: Optional[str] = settings.ESTADO_PENDIENTE
    dni: str

    @field_validator("hora")
    @classmethod
    def validar_hora_turno(cls, v: str) -> str:
        return validar_existencia_horaria(v)
    
    @field_validator("estado")
    @classmethod
    def validar_estado(cls, v: Optional[str]) -> Optional[str]:
        if v and v not in settings.ESTADOS_VALIDOS:
            raise ValueError(f"Estado inválido. Permitidos: {settings.ESTADOS_VALIDOS}")
        return v

class TurnoCreate(TurnoBase):
    persona_id: int

class TurnoUpdate(BaseModel):
    fecha: Optional[date] = None
    hora: Optional[str] = None
    estado: Optional[str] = None
    persona_id: Optional[int] = None

    @field_validator("hora")
    @classmethod
    def validar_hora_opcional(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        return validar_existencia_horaria(v)
    
    @field_validator("estado")
    @classmethod
    def validar_estado_opcional(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        if v not in settings.ESTADOS_VALIDOS:
             raise ValueError(f"Estado inválido. Permitidos: {settings.ESTADOS_VALIDOS}")
        return v
    
class TurnoOut(TurnoBase):
    id: int
    persona_id: int
    dni: str

    class Config:
        from_attributes = True

PersonaOut.model_rebuild()