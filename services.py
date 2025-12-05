from sqlalchemy.orm import Session
from datetime import date, timedelta
from typing import List
import models
from config import settings
import pandas as pd
import io
from decimal import Decimal
from borb.pdf import Document, Page, SingleColumnLayout, Paragraph, PDF
from borb.pdf import FixedColumnWidthTable, TableCell


def calcular_edad(fecha_nacimiento: date) -> int:
    today = date.today()
    return today.year - fecha_nacimiento.year - ((today.month, today.day) < (fecha_nacimiento.month, fecha_nacimiento.day))

def puede_sacar_turno(db: Session, persona_id: int) -> bool:
    seis_meses = date.today() - timedelta(days=182)
    cancelados = db.query(models.Turno).filter(
        models.Turno.persona_id == persona_id,
        models.Turno.estado == settings.ESTADO_CANCELADO,
        models.Turno.fecha >= seis_meses,
    ).count()
    return cancelados < 5

def turnos_disponibles(db: Session, fecha: date) -> List[str]:
    horarios_totales = settings.HORARIOS_VALIDOS.copy()
    
    ocupados_rows = db.query(models.Turno.hora).filter(
        models.Turno.fecha == fecha,
        models.Turno.estado != settings.ESTADO_CANCELADO,
    ).all()
    
    ocupados = [r[0] for r in ocupados_rows]
    disponibles = [h for h in horarios_totales if h not in ocupados]
    return disponibles 

def validar_estado_modificable(turno: models.Turno) -> str:
    
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

#-------- LÓGICA PARA REPORTES PDF CSV
def generar_csv_turnos_fecha(turnos_data: list) -> io.StringIO:
    data_list = []
    for t in turnos_data:
        data_list.append({
            "ID Turno": t.Turno.id,
            "Fecha": t.Turno.fecha,
            "Hora": t.Turno.hora,
            "Estado": t.Turno.estado,
            "Nombre Persona": t.nombre,
            "DNI Persona": t.dni
        })

    df = pd.DataFrame(data_list)

    stream = io.StringIO()
    df.to_csv(stream, index=False, sep=";")
    return stream

def generar_pdf_turnos_fecha(turnos_data: list, fecha: date) -> io.BytesIO:
    #Configuración de Borb
    pdf_buffer = io.BytesIO()
    doc = Document()
    page = Page()
    doc.add_page(page)
    layout = SingleColumnLayout(page)
    
    #Titulo
    layout.add(Paragraph(f"Reporte de turnos del día: {fecha}", font_size=Decimal(14)))
    
    table = FixedColumnWidthTable(number_of_rows=len(turnos_data) +1, number_of_columns=5)
    headers = ["ID", "Hora", "Estado", "Nombre", "DNI"]
    for h in headers:
        table.add(TableCell(Paragraph(h, font="Helvetica-Bold"), background_color=None))

    for t in turnos_data:
        table.add(TableCell(Paragraph(str(t.Turno.id))))
        table.add(TableCell(Paragraph(str(t.Turno.hora))))
        table.add(TableCell(Paragraph(str(t.Turno.estado))))
        table.add(TableCell(Paragraph(str(t.nombre))))
        table.add(TableCell(Paragraph(str(t.dni))))

    layout.add(table)
    
    PDF.dumps(pdf_buffer, doc)
    pdf_buffer.seek(0)
    return pdf_buffer

def generar_pdf_cancelados_mes(turnos: list, mes: str, anio: int) -> io.BytesIO:
    pdf_buffer = io.BytesIO()
    doc = Document()
    page = Page()
    doc.add_page(page)
    layout = SingleColumnLayout(page)
    
    layout.add(Paragraph(f"Turnos Cancelados - {mes} {anio}", font_size=Decimal(14)))
    layout.add(Paragraph(f"Total cancelados: {len(turnos)}", font_size=Decimal(10)))
    
    if turnos:
        # Tabla: ID, Fecha, Hora (3 columnas)
        table = FixedColumnWidthTable(number_of_rows=len(turnos) + 1, number_of_columns=3)
        
        # Encabezados
        for h in ["ID Turno", "Fecha", "Hora"]:
            table.add(TableCell(Paragraph(h, font="Helvetica-Bold")))

        # Filas
        for t in turnos:
            table.add(TableCell(Paragraph(str(t.id))))
            table.add(TableCell(Paragraph(str(t.fecha))))
            table.add(TableCell(Paragraph(str(t.hora))))

        layout.add(table)
    else:
        layout.add(Paragraph("No hay turnos cancelados en este período."))

    PDF.dumps(pdf_buffer, doc)
    pdf_buffer.seek(0)
    return pdf_buffer