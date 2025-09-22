from sqlalchemy import Column, Integer, String, Boolean, Date, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from datetime import date


class Persona(Base):
    __tablename__ = "personas"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    dni = Column(String, unique=True, nullable=False, index=True)
    telefono = Column(String, nullable=True)
    fecha_nacimiento = Column(Date, nullable=False)
    habilitado = Column(Boolean, default=True, nullable=False)

    turnos = relationship("Turno", back_populates="persona", cascade="all, delete-orphan")

class Turno(Base):
    __tablename__ = "turnos"

    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(Date, nullable=False, index=True)
    hora = Column(String, nullable=False)
    estado = Column(String, default="pendiente", nullable=False)
    persona_id = Column(Integer, ForeignKey("personas.id"), nullable=False)
    persona = relationship("Persona", back_populates="turnos")


