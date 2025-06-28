from db.database import DataBaseConnection
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import List, Optional
import uuid
import os
import shutil
from pathlib import Path
from datetime import datetime
from db.database import DataBaseConnection

db_connection = DataBaseConnection()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {
    "image": [".jpg", ".jpeg", ".png"],
    "document": [".pdf"]
}

class ProcessAnalyser:

    def __init__(self):
        pass

    def analyse(self, data):
        """Receber dados e tratar com OCR e LLM"""
        for item in data:
            print(item)

    def get_file_type(self, filename: str) -> str:
        """Determinar o tipo do arquivo baseado na extensão"""
        ext = Path(filename).suffix.lower()
        if ext in ALLOWED_EXTENSIONS["image"]:
            return "image"
        elif ext in ALLOWED_EXTENSIONS["document"]:
            return "document"
        return "unknown"

    def is_allowed_file(self, filename: str) -> bool:
        """Verificar se o arquivo é permitido"""
        ext = Path(filename).suffix.lower()
        all_extensions = ALLOWED_EXTENSIONS["image"] + ALLOWED_EXTENSIONS["document"]
        return ext in all_extensions

    async def save_upload_file(self, upload_file: UploadFile) -> dict:
        """Salvar arquivo carregado e retornar informações"""
        # Gerar ID único para o arquivo
        file_id = str(uuid.uuid4())
        
        # Manter extensão original
        file_extension = Path(upload_file.filename).suffix
        new_filename = f"{file_id}{file_extension}"
        file_path = UPLOAD_DIR / new_filename
        
        # Salvar arquivo
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
        
        # Obter tamanho do arquivo
        file_size = os.path.getsize(file_path)
        
        # Criar registro do arquivo
        file_record = {
            "id": file_id,
            "filename": new_filename,
            "original_filename": upload_file.filename,
            "file_type": self.get_file_type(upload_file.filename),
            "file_size": file_size,
            "upload_date": datetime.now().isoformat(),
            "file_path": str(file_path)
        }
        
        db_connection.colecao.insert_one(file_record)
        return file_record


