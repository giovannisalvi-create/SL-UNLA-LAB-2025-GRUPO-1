from database import Base, engine, SessionLocal
import models
from datetime import date, timedelta

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

db = SessionLocal()

# Persona 1: Cliente regular con varios turnos
p1 = models.Persona(
    nombre="Brian Rodríguez", 
    email="brian@gmail.com",
    dni="48351225",
    telefono="1189521452", 
    fecha_nacimiento=date(1996, 1, 1),
    habilitado=True
)

# Persona 2: Cliente con turnos confirmados
p2 = models.Persona(
    nombre="Mariano Cejas", 
    email="mariano.cejas@gmail.com",
    dni="42145961",
    telefono="1173334444", 
    fecha_nacimiento=date(1990, 6, 15),
    habilitado=True
)

# Persona 3: Cliente nuevo sin turnos previos
p3 = models.Persona(
    nombre="Giovanni Salvi", 
    email="giovanni.salvi@hotmail.com",
    dni="42157896",
    telefono="1167891234", 
    fecha_nacimiento=date(1998, 3, 22),
    habilitado=True
)

# Persona 4: Cliente deshabilitado (no puede sacar turnos)
p4 = models.Persona(
    nombre="Martin Scarfo", 
    email="scarfo.martin@yahoo.com",
    dni="39541236",
    telefono="1155558888", 
    fecha_nacimiento=date(1985, 12, 5),
    habilitado=False  
)

db.add_all([p1, p2, p3, p4])
db.commit()

hoy = date.today()
turnos = [
    # Turnos para Brian (persona_id=1)
    models.Turno(fecha=hoy, hora="09:00", estado="pendiente", persona_id=1),
    models.Turno(fecha=hoy, hora="09:30", estado="confirmado", persona_id=2),
    models.Turno(fecha=hoy - timedelta(days=30), hora="10:00", estado="cancelado", persona_id=1),
    models.Turno(fecha=hoy - timedelta(days=60), hora="11:00", estado="cancelado", persona_id=1),
    models.Turno(fecha=hoy - timedelta(days=90), hora="12:00", estado="cancelado", persona_id=1),
    models.Turno(fecha=hoy - timedelta(days=120), hora="13:00", estado="cancelado", persona_id=1),
    models.Turno(fecha=hoy - timedelta(days=150), hora="14:00", estado="pendiente", persona_id=1),
    
    # Turnos para Mariano (persona_id=2)
    models.Turno(fecha=hoy + timedelta(days=1), hora="10:00", estado="confirmado", persona_id=2),
    models.Turno(fecha=hoy + timedelta(days=7), hora="11:30", estado="pendiente", persona_id=2),
    models.Turno(fecha=hoy - timedelta(days=15), hora="15:00", estado="asistido", persona_id=2),  # Cambiado de 'atendido' a 'asistido'
    
    # Turno futuro para Lucía (persona_id=3) - Cliente nuevo
    models.Turno(fecha=hoy + timedelta(days=3), hora="16:00", estado="confirmado", persona_id=3),
    
    # Turno cancelado para Carlos (persona_id=4) - Cliente deshabilitado
    models.Turno(fecha=hoy - timedelta(days=10), hora="17:00", estado="cancelado", persona_id=4),
]

db.add_all(turnos)
db.commit()

db.close()
print("Base de datos cargada con datos de prueba")