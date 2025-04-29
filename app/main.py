from fastapi import FastAPI, Request, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
import socket

# Cargar variables de entorno
load_dotenv()

# Middleware para verificar la fuente de la solicitud
async def verify_request_from_apisix(request: Request):
    entorno = os.getenv("ENVIRONMENT")

    if entorno == "production":
        expected_url = os.getenv("APISIX_PROD")
        client_ip = request.client.host
        print(f"Client IP (Production): {client_ip}, Expected URL: {expected_url}")

        if not client_ip.startswith("http"):
            if client_ip != expected_url:
                raise HTTPException(status_code=403, detail="Forbidden: Not allowed source")
    else:
        # En local, resolver IP del contenedor 'apisix'
        expected_container_name = "apisix"
        expected_ip = socket.gethostbyname(expected_container_name)
        client_ip = request.client.host

        if client_ip != expected_ip:
            raise HTTPException(status_code=403, detail="Forbidden: Not allowed source")

# Crear la aplicación FastAPI
app = FastAPI(title="MyMind - Models Service", dependencies=[Depends(verify_request_from_apisix)])

# Conexión a MongoDB
MONGO_URI = os.getenv("MONGO_URI")
client = AsyncIOMotorClient(MONGO_URI)
db = client.get_database("mymind_users")  # Nombre de la BD

# Importar y registrar las rutas
from app.routes import transcriptions

app.include_router(transcriptions.router, prefix="/transcription", tags=["Transcriptions"])

# Ruta de prueba
@app.get("/")
async def root():
    return {"message": "Bienvenido al servicio de modelos de MyMind 🚀"}

