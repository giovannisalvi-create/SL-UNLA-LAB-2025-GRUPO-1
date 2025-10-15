# Sistema de gestión de turnos - Grupo 1


## Integrantes y endpoints asociados

**Brian Micael Rodríguez**
- `POST /personas` - Crear nueva persona
- `GET /personas` - Listar todas las personas
- `GET /personas/id` - Obtener persona por ID

**Mariano Hernan Cejas**
- `PUT /personas/id` - Actualizar persona
- `DELETE /personas/id` - Eliminar persona 
- `GET /turnos-disponibles?fecha=YYYY-MM-DD` - Consultar turnos disponibles

**Martín Pablo Scarfo**
- `POST /turnos` - Crear nuevo turno
- `GET /turnos` - Listar todos los turnos
- `GET /turnos/id` - Obtener turno por ID

**Giovanni Alejandro Salvi**
- `PUT /turnos/id` - Actualizar turno
- `DELETE /turnos/id` - Eliminar turno

## Instalación
```
- Instalar dependencias: pip install -r requirements.txt
- Inicializar DB con datos de prueba: python init_bd.py
- Levantar servidor: uvicorn main:app --reload
```

La aplicación estará disponible en: 
[http://localhost:8000](http://localhost:8000)

## Recursos
[Enlace hacia el video](https://vimeo.com/1121365102)

[Enlace a la colección de Postman](https://cejasm96-5484561.postman.co/workspace/SL-P---GRUPO-1's-Workspace~400713a7-73f3-45fe-8e48-c08af882d950/collection/48546434-10267aa8-e46d-467c-a444-37723e964e4d?action=share&creator=48546434)

## Estructura del proyecto
```
- main.py                   # Aplicación principal y endpoints
- database.py               # Configuración de la base de datos
- models.py                 # Modelos de Persona y Turno
- schemas.py                # Esquemas de Pydantic para validación
- crud.py                   # Operaciones de base de datos
- services.py               # Lógica de negocio y validaciones
- init_db.py                # Inicialización con datos de prueba
- requirements.txt          # Dependencias del proyecto
