from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, UploadFile, Form, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from pydantic import BaseModel
import shutil
import os
import uuid
from PIL import Image as PILImage, ExifTags
import magic  # Para detectar tipos de archivo ocultos
from stegano import lsb  # Librería para analizar esteganografía LSB

# Database Configuration
DATABASE_URL = "postgresql://user:password@db:5432/image_upload"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Models
class Image(Base):
    __tablename__ = "images"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, unique=True, nullable=False)
    alias = Column(String, nullable=False)
    status = Column(String, default="pending")  # pending, approved, rejected
    safe_to_publish = Column(Boolean, default=False)  # Análisis de esteganografía
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Initialize database
Base.metadata.create_all(bind=engine)

# FastAPI App
app = FastAPI()

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite solicitudes desde cualquier origen
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos los métodos (GET, POST, PUT, etc.)
    allow_headers=["*"],  # Permite todos los headers
)

UPLOAD_FOLDER = "uploaded_images"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Security Configuration
security = HTTPBasic()
ADMIN_TOKEN = "admin123"  # Token para el administrador

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Steganography Analysis
def analyze_image_for_steganography(file_path: str) -> bool:
    try:
        # Verificar metadatos de la imagen
        image = PILImage.open(file_path)
        metadata = image._getexif()  # Obtener metadatos EXIF
        if metadata:
            parsed_metadata = {ExifTags.TAGS.get(k, k): v for k, v in metadata.items() if k in ExifTags.TAGS}
            if "Software" in parsed_metadata or "Comments" in parsed_metadata:
                print(f"Metadata found: {parsed_metadata}")
                return False  # Marcar como sospechosa si hay metadatos problemáticos
        
        # Verificar datos ocultos con LSB
        hidden_data = lsb.reveal(file_path)
        if hidden_data:
            print(f"Hidden data detected: {hidden_data}")
            return False  # Marcar como sospechosa si hay datos ocultos
    except IndexError:
        # Sin datos ocultos, la imagen es segura
        return True
    except PILImage.UnidentifiedImageError:
        print("UnidentifiedImageError: La imagen no se pudo identificar correctamente.")
        return False  # Rechazar la imagen si no es válida
    except Exception as e:
        print(f"Error inesperado al analizar la imagen: {e}")
        return True  # Considerar segura si no se puede analizar completamente
    return True  # Imagen considerada segura si no se detecta contenido oculto

# Modelo para moderación
class ModerationRequest(BaseModel):
    status: str

@app.post("/upload/")
async def upload_image(file: UploadFile, alias: str = Form(...), db: SessionLocal = Depends(get_db)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Archivo inválido. Solo se permiten imágenes.")
    
    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
    
    # Guardar el archivo en el servidor
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Analizar esteganografía
    safe = analyze_image_for_steganography(file_path)

    if not safe:
        raise HTTPException(status_code=400, detail="Sospecha de imagen corrupta o dañada detectada y rechazada.")
    
    # Guardar en la base de datos
    new_image = Image(filename=unique_filename, alias=alias, safe_to_publish=safe)
    db.add(new_image)
    db.commit()
    db.refresh(new_image)
    
    return {"message": "Imagen cargada con exito", "image_id": new_image.id, "status": "Guardado para moderacion"}


@app.get("/gallery/")
def view_gallery(db: SessionLocal = Depends(get_db)):
    approved_images = db.query(Image).filter(Image.status == "approved", Image.safe_to_publish == True).all()
    return approved_images

@app.get("/pending/")
def list_pending_images(db: SessionLocal = Depends(get_db), credentials: HTTPBasicCredentials = Depends(security)):
    if credentials.password != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")
    pending_images = db.query(Image).filter(Image.status == "pending").all()
    return pending_images

@app.put("/moderate/{image_id}/")
def moderate_image(
    image_id: int,
    moderation_request: ModerationRequest,  # Recibe el status en el cuerpo de la solicitud
    db: SessionLocal = Depends(get_db),
    credentials: HTTPBasicCredentials = Depends(security)
):
    if credentials.password != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")

    status = moderation_request.status
    if status not in ["approved", "rejected"]:
        raise HTTPException(status_code=400, detail="Status Invalido. Usa 'approved' or 'rejected'.")

    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Imagen no encontrada")
    if not image.safe_to_publish and status == "approved":
        raise HTTPException(status_code=400, detail=" La imagen no es segura para publicar")
    image.status = status
    db.commit()
    db.refresh(image)
    return {"message": f"Image {status} successfully", "image_id": image.id}
