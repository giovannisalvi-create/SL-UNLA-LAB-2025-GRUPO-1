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
def generar_csv_turnos_fecha(lista_turnos: list) -> io.StringIO:
    contenido_csv = []
    for turno in lista_turnos:
        contenido_csv.append({
            "ID Turno": turno.Turno.id,
            "Fecha": turno.Turno.fecha,
            "Hora": turno.Turno.hora,
            "Estado": turno.Turno.estado,
            "Nombre Persona": turno.nombre,
            "DNI Persona": turno.dni
        })

    df = pd.DataFrame(contenido_csv)

    stream = io.StringIO()
    df.to_csv(stream, index=False, sep=";")
    return stream

def generar_pdf_turnos_fecha(lista_turnos: list, fecha: date) -> io.BytesIO:
    #Configuración de Borb
    pdf_buffer = io.BytesIO()
    documento = Document()
    pagina = Page()
    documento.add_page(pagina)
    layout = SingleColumnLayout(pagina)
    
    #Titulo
    layout.add(Paragraph(f"Reporte de turnos del día: {fecha}", font_size=Decimal(14)))
    
    table = FixedColumnWidthTable(number_of_rows=len(lista_turnos) +1, number_of_columns=5)
    encabezados = ["ID", "Hora", "Estado", "Nombre", "DNI"]
    for encabezado in encabezados:
        table.add(TableCell(Paragraph(encabezado, font="Helvetica-Bold"), background_color=None))

    for turno in lista_turnos:
        table.add(TableCell(Paragraph(str(turno.Turno.id))))
        table.add(TableCell(Paragraph(str(turno.Turno.hora))))
        table.add(TableCell(Paragraph(str(turno.Turno.estado))))
        table.add(TableCell(Paragraph(str(turno.nombre))))
        table.add(TableCell(Paragraph(str(turno.dni))))

    layout.add(table)
    
    PDF.dumps(pdf_buffer, documento)
    pdf_buffer.seek(0)
    return pdf_buffer

def generar_pdf_cancelados_mes(lista_turnos: list, mes: str, anio: int) -> io.BytesIO:
    pdf_buffer = io.BytesIO()
    documento = Document()
    pagina = Page()
    documento.add_page(pagina)
    layout = SingleColumnLayout(pagina)
    
    layout.add(Paragraph(f"Turnos Cancelados - {mes} {anio}", font_size=Decimal(14)))
    layout.add(Paragraph(f"Total cancelados: {len(lista_turnos)}", font_size=Decimal(10)))
    
    if lista_turnos:
        # Tabla: ID, Fecha, Hora (3 columnas)
        table = FixedColumnWidthTable(number_of_rows=len(lista_turnos) + 1, number_of_columns=3)
        
        # Encabezados
        for encabezado in ["ID Turno", "Fecha", "Hora"]:
            table.add(TableCell(Paragraph(encabezado, font="Helvetica-Bold")))

        # Filas
        for turno in lista_turnos:
            table.add(TableCell(Paragraph(str(turno.id))))
            table.add(TableCell(Paragraph(str(turno.fecha))))
            table.add(TableCell(Paragraph(str(turno.hora))))

        layout.add(table)
    else:
        layout.add(Paragraph("No hay turnos cancelados en este período."))

    PDF.dumps(pdf_buffer, documento)
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
    df.to_csv(buffer, index=False, sep=";")
    buffer.seek(0)
    return buffer


def generar_csv_turnos_persona_paginado(
    turnos,
    persona,
    pagina: int,
    tamanio: int,
    total_paginas: int,
    total_turnos: int
) -> io.StringIO:

    buffer = io.StringIO()

    buffer.write("# Reporte de Turnos por Persona\n")
    buffer.write(
        f"# Persona: {persona.nombre} - DNI {persona.dni}\n"
    )
    buffer.write(
        f"# Pagina: {pagina} de {total_paginas} "
        f"- Tamanio pagina: {tamanio} "
        f"- Total turnos: {total_turnos}\n"
    )


    data = []
    for turno, nombre, dni in turnos:
        data.append({
            "Nombre": nombre,
            "DNI": dni,
            "Fecha": turno.fecha,
            "Hora": turno.hora,
            "Estado": turno.estado
        })

    df = pd.DataFrame(data)

    df.to_csv(buffer, index=False, sep=";")
    buffer.seek(0)
    return buffer


def generar_pdf_turnos_persona_paginado(
    turnos,
    persona,
    pagina: int,
    tamanio: int,
    total_paginas: int,
    total_turnos: int
):
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

    layout.add(
        Paragraph(
            f"Página {pagina} de {total_paginas} | "
            f"Tamaño página: {tamanio} | "
            f"Total turnos: {total_turnos}",
            font_size=Decimal(9)
        )
    )

    table = FixedColumnWidthTable(
        number_of_rows=len(turnos) + 1,
        number_of_columns=5
    )

    headers = ["Nombre", "DNI", "Fecha", "Hora", "Estado"]
    for h in headers:
        table.add(TableCell(Paragraph(h, font="Helvetica-Bold")))

    for turno, nombre, dni in turnos:
        table.add(TableCell(Paragraph(nombre)))
        table.add(TableCell(Paragraph(str(dni))))
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
    buffer = io.StringIO()
    
    # Crear DataFrame con datos esenciales
    data = []
    for persona in resultado:
        data.append({
            "ID": persona["id"],
            "DNI": persona["dni"],
            "Nombre": persona["nombre"],
            "Estado": persona["estado_general"],
            "Telefono": persona["telefono"],
            "Habilitado": "Si" if persona["habilitado"] else "No",
            "Puede sacar turno": "Si" if persona["puede_sacar_turno"] else "No",
            "Email": persona["email"]
            
        })
    
    df = pd.DataFrame(data)
    buffer.write('\ufeff')
    df.to_csv(
        buffer,
        index=False,
        sep=";",
        encoding='utf-8-sig'
    )
    
    buffer.seek(0)
    return buffer

def generar_pdf_turnos_confirmados_periodos(resultados: list, desde: date, hasta: date, 
    pagina: int, total_paginas: int, total: int) -> io.BytesIO:
    
    def preparar_texto_pdf(texto: any, max_len: int = 25) -> str:
        if texto is None:
            return ""
        
        texto_str = str(texto)
        if len(texto_str) > max_len and "@" in texto_str:
            usuario, dominio = texto_str.split("@", 1)
            if len(usuario) > 20:
                usuario = usuario[:17] + "..."
            texto_str = f"{usuario}\n@{dominio}"
        elif len(texto_str) > max_len:
            lineas = [texto_str[i:i+max_len] for i in range(0, len(texto_str), max_len)]
            texto_str = "\n".join(lineas)
        
        return texto_str
    
    #Crear PDF
    pdf_buffer = io.BytesIO()
    doc = Document()
    page = Page()
    doc.add_page(page)
    layout = SingleColumnLayout(page)
    
    #Título
    layout.add(Paragraph(f"Reporte de Turnos Confirmados", font_size=Decimal(16)))
    layout.add(Paragraph(f"Período: {desde} a {hasta}", font_size=Decimal(12)))
    layout.add(Paragraph(f"Página {pagina} de {total_paginas} - Total de turnos: {total}", 
                        font_size=Decimal(10)))
    layout.add(Paragraph(f"Fecha de generación: {date.today()}", font_size=Decimal(10)))
    
    if resultados:
        #Tabla con anchos optimizados
        table = FixedColumnWidthTable(
            number_of_rows=len(resultados) + 1,
            number_of_columns=7,
            column_widths=[
                Decimal(1),   # ID
                Decimal(3),   # Fecha
                Decimal(2.5), # Hora
                Decimal(3),   # Estado
                Decimal(4),   # Nombre
                Decimal(2.5),   # DNI
                Decimal(4)  # Email
            ]
        )
        
        # Encabezados
        headers = ["ID", "Fecha", "Hora", "Estado", "Nombre", "DNI", "Email"]
        for h in headers:
            table.add(TableCell(Paragraph(h, font="Helvetica-Bold")))
        
        for item in resultados:
            table.add(TableCell(Paragraph(str(item["id"]))))
            table.add(TableCell(Paragraph(str(item["fecha"]))))
            table.add(TableCell(Paragraph(str(item["hora"]))))
            table.add(TableCell(Paragraph(str(item["estado"]))))
            table.add(TableCell(Paragraph(preparar_texto_pdf(item["nombre_persona"], 20))))
            table.add(TableCell(Paragraph(str(item["dni_persona"]))))
            table.add(TableCell(Paragraph(preparar_texto_pdf(item["email_persona"], 25))))
        
        layout.add(table)
    else:
        layout.add(Paragraph("No hay turnos confirmados en este período."))
    
    PDF.dumps(pdf_buffer, doc)
    pdf_buffer.seek(0)
    return pdf_buffer


def generar_csv_turnos_confirmados_periodos(resultados: list, desde: date, hasta: date,
    pagina: int, total_paginas: int, total: int) -> io.StringIO:
    buffer = io.StringIO()
    
    data = []
    for item in resultados:
        data.append({
            "ID_Turno": item["id"],
            "Fecha": item["fecha"],
            "Hora": item["hora"],
            "Estado": item["estado"],
            "ID_Persona": item["persona_id"],
            "DNI": item["dni_persona"],
            "Nombre": item["nombre_persona"],
            "Email": item["email_persona"]
        })
    
    df = pd.DataFrame(data)
    buffer.write('\ufeff')
    
    df.to_csv(
        buffer,
        index=False,
        sep=";",
        encoding='utf-8-sig'
    )
    
    buffer.seek(0)
    return buffer