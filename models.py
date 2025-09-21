from sqlalchemy import Column, Integer, String, Boolean, Date
from database import Base


class Persona(Base):
    __tablename__ = "personas"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    dni = Column(String, unique=True, nullable=False, index=True)
    telefono = Column(String, nullable=True)
    fecha_nacimiento = Column(Date, nullable=False)
    habilitado = Column(Boolean, default=True, nullable=False)