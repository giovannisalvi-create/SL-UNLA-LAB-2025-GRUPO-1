from fastapi import FastAPI
from database import Base, engine

Base.metadata.create_all(bind=engine)
app = FastAPI(title="TP - API de Turnos")

@app.get("/", include_in_schema=False)
def root():
    return {"mensaje": "API de turnos funcionando. Ir a /docs para la documentación."}
