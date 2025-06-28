from pydantic import BaseModel
from typing import List, Optional, Annotated

from uuid import UUID
from fastapi import UploadFile, File, Form

# Modelos Pydantic
class Item(BaseModel):
    request_id: UUID = Form(...) # UUID
    listFiles: Annotated[bytes, File()] = Form(...)
    query: Optional[str] = Form(None) # Prompt para ser processado
    user_id: str = Form(...) # Identificador do solicitante


class ItemResponse(BaseModel):
    query: str = Form(None) # Prompt para ser processado
    candidates: str = Form(None) # Melhores curriculos que se enquadram na vaga
    explainAbout: str = Form(None) # Justificativa sobre o prompt ou resumo de cada curriculo

class FileUploadResponse(BaseModel):
    id: str
    filename: str
    original_filename: str
    file_type: str
    file_size: int
    upload_date: str
    file_path: str

class FileInfo(BaseModel):
    id: str
    filename: str
    original_filename: str
    file_type: str
    file_size: int
    upload_date: str
