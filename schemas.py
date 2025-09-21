from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date

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