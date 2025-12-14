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

def generar_csv_turnos_cancelados_mes(turnos: list, mes: str, anio: int) -> io.StringIO:

    data = []
    for t in turnos:
        data.append({
            "ID Turno": t.id,
            "Persona ID": t.persona_id,
            "Fecha": t.fecha,
            "Hora": t.hora,
            "Estado": t.estado
        })

    df = pd.DataFrame(data)

    buffer = io.StringIO()
    df.to_csv(buffer, index=False, sep=",")
    buffer.seek(0)
    return buffer


def generar_csv_turnos_persona_paginado(turnos, persona):

    data = []

    for turno, nombre, dni in turnos:
        data.append({
            "ID Persona": persona.id,
            "Nombre": nombre,
            "DNI": dni,
            "ID Turno": turno.id,
            "Fecha": turno.fecha,
            "Hora": turno.hora,
            "Estado": turno.estado
        })

    df = pd.DataFrame(data)

    buffer = io.StringIO()
    df.to_csv(buffer, index=False, sep=",")
    buffer.seek(0)
    return buffer

def generar_pdf_turnos_persona_paginado(turnos, persona):
    buffer = io.BytesIO()
    doc = Document()

    page = Page()
    doc.add_page(page)
    layout = SingleColumnLayout(page)

    layout.add(
        Paragraph(
            f"Reporte de Turnos - {persona.nombre} (DNI {persona.dni})",
            font_size=Decimal(14)
        )
    )

    table = FixedColumnWidthTable(
        number_of_rows=len(turnos) + 1,
        number_of_columns=7
    )

    headers = ["ID Persona", "Nombre","DNI","ID Turno", "Fecha", "Hora", "Estado"]
    for h in headers:
        table.add(TableCell(Paragraph(h, font="Helvetica-Bold")))

    for turno, nombre, dni in turnos:
        table.add(TableCell(Paragraph(str(persona.id))))
        table.add(TableCell(Paragraph(nombre)))
        table.add(TableCell(Paragraph(str(dni))))
        table.add(TableCell(Paragraph(str(turno.id))))
        table.add(TableCell(Paragraph(str(turno.fecha))))
        table.add(TableCell(Paragraph(str(turno.hora))))
        table.add(TableCell(Paragraph(str(turno.estado))))

    layout.add(table)

    PDF.dumps(buffer, doc)
    buffer.seek(0)
    return buffer

def generar_csv_turnos_cancelados(turnos: list) -> io.StringIO:
    data_list = []

    for t in turnos:
        data_list.append({
            "ID Turno": t.id,
            "Fecha": t.fecha,
            "Hora": t.hora,
            "Estado": t.estado,
            "Persona ID": t.persona_id
        })

    df = pd.DataFrame(data_list)

    stream = io.StringIO()
    df.to_csv(stream, index=False, sep=";")
    return stream

def generar_pdf_turnos_cancelados(turnos: list) -> io.BytesIO:
    pdf_buffer = io.BytesIO()
    doc = Document()
    page = Page()
    doc.add_page(page)
    layout = SingleColumnLayout(page)

    layout.add(Paragraph("Reporte de Turnos Cancelados", font_size=Decimal(14)))
    layout.add(Paragraph(f"Total de turnos cancelados: {len(turnos)}", font_size=Decimal(10)))

    if turnos:
        table = FixedColumnWidthTable(
            number_of_rows=len(turnos) + 1,
            number_of_columns=4
        )

        for h in ["ID", "Fecha", "Hora", "Persona ID"]:
            table.add(TableCell(Paragraph(h, font="Helvetica-Bold")))

        for t in turnos:
            table.add(TableCell(Paragraph(str(t.id))))
            table.add(TableCell(Paragraph(str(t.fecha))))
            table.add(TableCell(Paragraph(str(t.hora))))
            table.add(TableCell(Paragraph(str(t.persona_id))))

        layout.add(table)
    else:
        layout.add(Paragraph("No hay turnos cancelados."))

    PDF.dumps(pdf_buffer, doc)
    pdf_buffer.seek(0)
    return pdf_buffer

def generar_pdf_estado_personas(personas_data: list) -> io.BytesIO:
    pdf_buffer = io.BytesIO()
    doc = Document()
    page = Page()
    doc.add_page(page)
    layout = SingleColumnLayout(page)

    layout.add(Paragraph("Reporte Estado de Personas", font_size=Decimal(14)))

    table = FixedColumnWidthTable(
        number_of_rows=len(personas_data) + 1,
        number_of_columns=5
    )

    for h in ["ID", "Nombre", "DNI", "Email", "Estado"]:
        table.add(TableCell(Paragraph(h, font="Helvetica-Bold")))

    def partir_texto(texto: str, largo: int = 12) -> str:
        return "\n".join(
            texto[i:i+largo] for i in range(0, len(texto), largo)
        )

    for p in personas_data:
        table.add(TableCell(Paragraph(str(p["id"]))))
        table.add(TableCell(Paragraph(p["nombre"])))
        table.add(TableCell(Paragraph(p["dni"])))
        table.add(TableCell(Paragraph(partir_texto(p["email"]))))
        table.add(TableCell(Paragraph(p["estado_general"])))

    layout.add(table)

    PDF.dumps(pdf_buffer, doc)
    pdf_buffer.seek(0)
    return pdf_buffer

def generar_csv_estado_personas(resultado: list, pagina: int, total_paginas: int) -> io.StringIO:
    """
    Genera un archivo CSV con el estado de las personas
    """
    buffer = io.StringIO()
    
    # Crear DataFrame con los datos
    data = []
    for persona in resultado:
        data.append({
            "ID": persona["id"],
            "Nombre": persona["nombre"],
            "DNI": persona["dni"],
            "Email": persona["email"],
            "Telefono": persona["telefono"],
            "Habilitado": "Sí" if persona["habilitado"] else "No",
            "Puede sacar turno": "Sí" if persona["puede_sacar_turno"] else "No",
            "Estado General": persona["estado_general"]
        })
    
    df = pd.DataFrame(data)
    
    # Agregar información de paginación como comentario al inicio del CSV
    header_info = f"# Reporte de Estado de Personas - Página {pagina} de {total_paginas}\n"
    header_info += f"# Total de registros en esta página: {len(resultado)}\n"
    header_info += f"# Fecha de generación: {date.today()}\n\n"
    
    buffer.write(header_info)
    df.to_csv(buffer, index=False, sep=";")
    
    buffer.seek(0)
    return buffer


def generar_pdf_turnos_confirmados_periodos(resultados: list, desde: date, hasta: date, 
                                          pagina: int, total_paginas: int, total: int) -> io.BytesIO:
    """
    Genera un PDF con los turnos confirmados en un período específico
    """
    
    # Función interna para manejar texto (tildes y división)
    def preparar_texto(texto: any, max_len: int = 25) -> str:
        """Prepara texto para PDF: maneja tildes y divide si es muy largo"""
        if texto is None:
            return ""
        
        texto_str = str(texto)
        
        # SOLUCIÓN TILDES: Convertir "José María" → "Jose Maria"
        try:
            import unicodedata
            # Normalizar y remover acentos
            texto_normalizado = unicodedata.normalize('NFKD', texto_str)
            texto_sin_acentos = ''.join(
                c for c in texto_normalizado 
                if not unicodedata.combining(c)
            )
            texto_str = texto_sin_acentos
        except:
            pass  # Si falla, usar texto original
        
        # SOLUCIÓN EMAIL LARGO: Dividir si es muy largo
        if len(texto_str) > max_len and "@" in texto_str:
            # Para emails: partir antes del @
            usuario, dominio = texto_str.split("@", 1)
            if len(usuario) > 20:
                usuario = usuario[:17] + "..."
            texto_str = f"{usuario}\n@{dominio}"
        elif len(texto_str) > max_len:
            # Para otros textos: dividir en líneas
            lineas = [texto_str[i:i+max_len] for i in range(0, len(texto_str), max_len)]
            texto_str = "\n".join(lineas)
        
        return texto_str
    
    # Crear PDF
    pdf_buffer = io.BytesIO()
    doc = Document()
    page = Page()
    doc.add_page(page)
    layout = SingleColumnLayout(page)
    
    # Título del reporte
    layout.add(Paragraph(f"Reporte de Turnos Confirmados", font_size=Decimal(16)))
    layout.add(Paragraph(f"Período: {desde} a {hasta}", font_size=Decimal(12)))
    layout.add(Paragraph(f"Página {pagina} de {total_paginas} - Total de turnos: {total}", 
                        font_size=Decimal(10)))
    layout.add(Paragraph(f"Fecha de generación: {date.today()}", font_size=Decimal(10)))
    
    if resultados:
        # Crear tabla con anchos optimizados
        table = FixedColumnWidthTable(
            number_of_rows=len(resultados) + 1,
            number_of_columns=7,
            column_widths=[
                Decimal(1),   # ID
                Decimal(2),   # Fecha
                Decimal(1.5), # Hora
                Decimal(2),   # Estado
                Decimal(3),   # Nombre
                Decimal(2),   # DNI
                Decimal(3.5)  # Email (más ancho)
            ]
        )
        
        # ENCABEZADOS
        headers = ["ID", "Fecha", "Hora", "Estado", "Nombre", "DNI", "Email"]
        for h in headers:
            table.add(TableCell(
                Paragraph(preparar_texto(h), font="Helvetica-Bold")
            ))
        
        # DATOS
        for item in resultados:
            table.add(TableCell(Paragraph(preparar_texto(item["id"]))))
            table.add(TableCell(Paragraph(preparar_texto(item["fecha"]))))
            table.add(TableCell(Paragraph(preparar_texto(item["hora"]))))
            table.add(TableCell(Paragraph(preparar_texto(item["estado"]))))
            table.add(TableCell(Paragraph(preparar_texto(item["nombre_persona"], 20))))
            table.add(TableCell(Paragraph(preparar_texto(item["dni_persona"]))))
            table.add(TableCell(Paragraph(preparar_texto(item["email_persona"], 25))))
        
        layout.add(table)
    else:
        layout.add(Paragraph("No hay turnos confirmados en este período."))
    
    # Generar PDF
    PDF.dumps(pdf_buffer, doc)
    pdf_buffer.seek(0)
    
    return pdf_buffer


def generar_csv_turnos_confirmados_periodos(resultados: list, desde: date, hasta: date,
                                          pagina: int, total_paginas: int, total: int) -> io.StringIO:
    """
    Genera un CSV con los turnos confirmados en un período específico
    """
    buffer = io.StringIO()
    
    # Encabezado informativo
    header_info = f"# Reporte de Turnos Confirmados\n"
    header_info += f"# Período: {desde} a {hasta}\n"
    header_info += f"# Página {pagina} de {total_paginas} - Total de turnos: {total}\n"
    header_info += f"# Fecha de generación: {date.today()}\n\n"
    
    buffer.write(header_info)
    
    # Crear DataFrame
    data = []
    for item in resultados:
        data.append({
            "ID Turno": item["id"],
            "Fecha": item["fecha"],
            "Hora": item["hora"],
            "Estado": item["estado"],
            "Persona ID": item["persona_id"],
            "Nombre": item["nombre_persona"],
            "DNI": item["dni_persona"],
            "Email": item["email_persona"]
        })
    
    df = pd.DataFrame(data)
    df.to_csv(buffer, index=False, sep=";")
    
    buffer.seek(0)
    return buffer
