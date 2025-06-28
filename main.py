from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from uuid import UUID
from db.squema import *
from process.reader import ProcessAnalyser
import os
import shutil
from pathlib import Path


process_analyser = ProcessAnalyser()


# Criar instância do FastAPI
app = FastAPI(
    title="API TechMatch",
    description="Leitura inteligente de leitura de documentos",
    version="1.0.0"
)

# Rotas
@app.get("/")
def read_root():
    """Rota principal da API"""
    return {"message": "Bem-vindo à minha API!", "version": "1.0.0"}

@app.get("/health")
def health_check():
    """Endpoint para verificar se a API está funcionando"""
    return {"status": "healthy", "message": "API está funcionando corretamente"}

@app.post("/analyse/", response_model=ItemResponse, tags=["Items"])
def create_item(
    query: str = Form(..., description="String de consulta para processamento"),
    request_id: str = Form(..., description="ID único da requisição (UUID)"),
    user_id: str = Form(..., description="ID do usuário solicitante"),
    files: List[UploadFile] = File(..., description="Lista de arquivos (PDF, JPG, PNG)")
    ):
    """Recebe multiplos documentos como PDFs ou Imagens (JPEG/PNG)"""
    result = process_analyser.analyse(request_id, files, query, user_id)
    
    return result


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)