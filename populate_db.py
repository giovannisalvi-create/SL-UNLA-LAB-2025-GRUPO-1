import random
from datetime import date, timedelta
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
import models
from config import settings

# --- CONFIGURACIÓN VISUAL ---
GREEN = "\033[92m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"

def init_db():
    print(f"{CYAN}--- Inicializando Esquema de Base de Datos ---{RESET}")
    Base.metadata.create_all(bind=engine)

def get_or_create_persona(db: Session, nombre, apellido, dni, habilitado=True):
    """
    Busca una persona por DNI. Si no existe, la crea.
    """
    email = f"{nombre.lower()}.{apellido.lower()}@email.com"
    persona = db.query(models.Persona).filter(models.Persona.dni == dni).first()
    
    if not persona:
        persona = models.Persona(
            nombre=f"{nombre} {apellido}",
            email=email,
            dni=dni,
            telefono=f"11{random.randint(40000000, 99999999)}",
            fecha_nacimiento=date(random.randint(1980, 2000), random.randint(1, 12), random.randint(1, 28)),
            habilitado=habilitado
        )
        db.add(persona)
        db.commit()
        db.refresh(persona)
        estado_str = "Habilitado" if habilitado else "Inhabilitado"
        print(f"  + Registrado: {nombre} {apellido} (DNI: {dni}) - {estado_str}")
    else:
        # print(f"  . Existente: {nombre} {apellido} (DNI: {dni})") # Comentado para menos ruido
        pass
    
    return persona

def generar_datos_prueba(db: Session):
    print(f"\n{CYAN}--- Generando Personas ---{RESET}")
    
    # 1. Personas Clave
    p_paginacion = get_or_create_persona(db, "Lucas", "Rodriguez", "11111111")
    p_cancelaciones = get_or_create_persona(db, "Sofia", "Martinez", "22222222")
    p_inhabilitado = get_or_create_persona(db, "Miguel", "Torres", "33333333", habilitado=False)
    
    # 2. Personas Extra para rellenar los 25 turnos de hoy
    personas_extra = []
    nombres_extra = ["Ana", "Carlos", "Elena", "Diego", "Valentina", "Facundo", "Jimena", "Pablo"]
    for i, nombre in enumerate(nombres_extra):
        dni = f"444444{i:02d}"
        p = get_or_create_persona(db, nombre, "Generico", dni)
        personas_extra.append(p)

    pool_personas = [p_paginacion, p_cancelaciones] + personas_extra

    print(f"\n{CYAN}--- Generando Turnos ---{RESET}")
    turnos_creados = 0
    horarios = settings.HORARIOS_VALIDOS
    estados_validos = settings.ESTADOS_VALIDOS # [pendiente, confirmado, cancelado, asistido]
    hoy = date.today()

    # =========================================================================
    # [cite_start]ESCENARIO A: 25 TURNOS PARA HOY (Para probar Paginación por Fecha) [cite: 6]
    # =========================================================================
    print(f"{YELLOW}> Generando 25 turnos variados para HOY ({hoy})...{RESET}")
    
    CANTIDAD_A_GENERAR = 25
    
    for i in range(CANTIDAD_A_GENERAR):
        # 1. Ciclamos los horarios: si hay 16 horarios y i=17, vuelve a empezar (simula turno simultáneo)
        horario = horarios[i % len(horarios)]
        
        # 2. Elegimos persona al azar
        persona = random.choice(pool_personas)
        
        # 3. Elegimos estado al azar
        estado = random.choice(estados_validos)
        
        # Evitamos duplicados exactos (misma persona a la misma hora)
        if not db.query(models.Turno).filter_by(fecha=hoy, hora=horario, persona_id=persona.id).first():
            t = models.Turno(
                fecha=hoy,
                hora=horario,
                estado=estado,
                persona_id=persona.id
            )
            db.add(t)
            turnos_creados += 1

    # =========================================================================
    # ESCENARIO B: Historial Lucas (Paginación por Persona)
    # =========================================================================
    print(f"{YELLOW}> Generando historial para Lucas Rodriguez...{RESET}")
    for i in range(25):
        fecha_atras = hoy - timedelta(days=(i+1)*2)
        horario = random.choice(horarios)
        if not db.query(models.Turno).filter_by(fecha=fecha_atras, hora=horario).first():
            t = models.Turno(
                fecha=fecha_atras,
                hora=horario,
                estado=settings.ESTADO_ASISTIDO,
                persona_id=p_paginacion.id
            )
            db.add(t)
            turnos_creados += 1

    # =========================================================================
    # ESCENARIO C: Cancelaciones Sofia (Bloqueo Lógico y Reporte Mensual)
    # =========================================================================
    print(f"{YELLOW}> Generando cancelaciones para Sofia Martinez...{RESET}")
    # 3 este mes
    for i in range(1, 4):
        fecha = date(hoy.year, hoy.month, i)
        if not db.query(models.Turno).filter_by(fecha=fecha, hora=horarios[0]).first():
            t = models.Turno(fecha=fecha, hora=horarios[0], estado=settings.ESTADO_CANCELADO, persona_id=p_cancelaciones.id)
            db.add(t)
            turnos_creados += 1
    # 3 mes pasado
    fecha_mes_pasado = hoy.replace(day=1) - timedelta(days=1)
    for i in range(1, 4):
        fecha = date(fecha_mes_pasado.year, fecha_mes_pasado.month, i)
        if not db.query(models.Turno).filter_by(fecha=fecha, hora=horarios[1]).first():
            t = models.Turno(fecha=fecha, hora=horarios[1], estado=settings.ESTADO_CANCELADO, persona_id=p_cancelaciones.id)
            db.add(t)
            turnos_creados += 1

    # =========================================================================
    # ESCENARIO D: Confirmados Periodo (Reporte Giovanni)
    # =========================================================================
    print(f"{YELLOW}> Generando confirmados semana pasada...{RESET}")
    inicio_semana = hoy - timedelta(days=7)
    for i in range(5):
        fecha = inicio_semana + timedelta(days=i)
        p = personas_extra[i % len(personas_extra)]
        if not db.query(models.Turno).filter_by(fecha=fecha, hora="10:00").first():
            t = models.Turno(fecha=fecha, hora="10:00", estado=settings.ESTADO_CONFIRMADO, persona_id=p.id)
            db.add(t)
            turnos_creados += 1

    db.commit()
    print(f"{GREEN}✅ Base de datos actualizada. Total nuevos insertados: {turnos_creados}{RESET}")

def main():
    db = SessionLocal()
    try:
        init_db()
        generar_datos_prueba(db)
        
        print(f"\n{GREEN}=== CASOS DE PRUEBA LISTOS ==={RESET}")
        print(f"1. {CYAN}Turnos por Fecha (HOY):{RESET} Se generaron ~25 turnos para la fecha '{date.today()}'.")
        print(f"   Prueba: ...?fecha={date.today()}&pagina=1&cantidad=10 (Debe haber pag. 1, 2 y 3)")
        print(f"2. {CYAN}Cancelados Mes:{RESET} Sofia Martinez tiene cancelados este mes.")
        print(f"3. {CYAN}Historial Persona:{RESET} DNI 11111111 tiene historial extenso.")
        
    except Exception as e:
        print(f"{GREEN}Error:{RESET} {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()