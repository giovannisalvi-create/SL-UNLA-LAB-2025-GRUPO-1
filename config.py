import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

class Config:
    INICIO = int(os.getenv("HORARIO_INICIO", 9))
    FIN = int(os.getenv("HORARIO_FIN", 17))
    INTERVALO = int(os.getenv("INTERVALO_MINUTOS", 30))
    
    _estados_str = os.getenv("ESTADOS", "pendiente,confirmado,cancelado,asistido")
    ESTADOS_VALIDOS = [e.strip().lower() for e in _estados_str.split(",")]
    
    ESTADO_PENDIENTE = "pendiente"
    ESTADO_CONFIRMADO = "confirmado"
    ESTADO_CANCELADO = "cancelado"
    ESTADO_ASISTIDO = "asistido"
    
    HORARIOS_VALIDOS = []
    
    _hora_actual = datetime.strptime(str(INICIO), "%H")
    _hora_fin = datetime.strptime(str(FIN), "%H")
    
    while _hora_actual < _hora_fin:
        HORARIOS_VALIDOS.append(_hora_actual.strftime("%H:%M"))
        _hora_actual += timedelta(minutes=INTERVALO)
        
settings = Config()