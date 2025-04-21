import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Leer la URI de MongoDB desde el archivo .env
MONGO_URI = os.getenv("MONGO_URI")

# Conectar con la base de datos en la nube
client = AsyncIOMotorClient(MONGO_URI)
db = client["myMindDB-Users"]  
users_collection = db["users"]
