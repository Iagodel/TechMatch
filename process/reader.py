from db.database import DataBaseConnection
from fastapi import HTTPException, UploadFile
from typing import List
import uuid
import os
import tempfile
from pathlib import Path
from datetime import datetime
import easyocr
from transformers import pipeline
from pdf2image import convert_from_bytes

db_connection = DataBaseConnection()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {
    "image": [".jpg", ".jpeg", ".png"],
    "document": [".pdf"]
}

MAX_FILE_SIZE = 10 * 1024 * 1024

class ProcessAnalyser:
    def __init__(self):
        self.summarizer = pipeline("summarization", model="Falconsai/text_summarization")
        self.qa = pipeline("question-answering", model="deepset/roberta-base-squad2")
        self.reader = easyocr.Reader(['pt', 'en'])

    async def analyse(self, files: List[UploadFile], query: str, user_id: str):
        if not files or len(files) == 0:
            raise HTTPException(status_code=400, detail="Pelo menos um arquivo deve ser enviado")
        if len(files) > 20:
            raise HTTPException(status_code=400, detail="Máximo de 20 arquivos por requisição")
        if not query.strip():
            raise HTTPException(status_code=400, detail="Campo 'query' não pode estar vazio")
        if not user_id.strip():
            raise HTTPException(status_code=400, detail="Campo 'user_id' não pode estar vazio")

        uploaded_files = []
        request_id = str(uuid.uuid4())

        for file in files:
            if not file.filename:
                raise HTTPException(status_code=400, detail="Arquivo sem nome encontrado")
            if not self.is_allowed_file(file.filename):
                raise HTTPException(
                    status_code=400,
                    detail=f"Arquivo '{file.filename}' não é permitido. Tipos aceitos: {', '.join(ALLOWED_EXTENSIONS['image'] + ALLOWED_EXTENSIONS['document'])}"
                )

            file.file.seek(0, 2)
            file_size = file.file.tell()
            file.file.seek(0)
            if file_size > MAX_FILE_SIZE:
                raise HTTPException(status_code=400, detail=f"Arquivo '{file.filename}' é muito grande. Tamanho máximo: {MAX_FILE_SIZE // (1024*1024)}MB")

            try:
                content = await file.read()
                texto_extraido = self.extract_text(content, file.filename)
                result = self.process_text(texto_extraido, query=query)
                uploaded_files.append({
                    "filename": file.filename,
                    "resultado": result
                })
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Erro ao processar arquivo '{file.filename}': {str(e)}")

        request_record = {
            "request_id": request_id,
            "user_id": user_id,
            "query": query,
            "files": uploaded_files,
            "files_count": len(uploaded_files),
            "created_at": datetime.now().isoformat(),
            "status": "received"
        }

        db_connection.colecao.insert_one(request_record)

        return {
            "request_id": request_id,
            "user_id": user_id,
            "query": query,
            "files": uploaded_files,
            "created_at": request_record["created_at"],
            "status": request_record["status"]
        }

    def get_file_type(self, filename: str) -> str:
        ext = Path(filename).suffix.lower()
        if ext in ALLOWED_EXTENSIONS["image"]:
            return "image"
        elif ext in ALLOWED_EXTENSIONS["document"]:
            return "document"
        return "unknown"

    def is_allowed_file(self, filename: str) -> bool:
        ext = Path(filename).suffix.lower()
        all_extensions = ALLOWED_EXTENSIONS["image"] + ALLOWED_EXTENSIONS["document"]
        return ext in all_extensions

    def process_text(self, texto_extraido: str, query=None):
        if query:
            answer = self.qa(question=query, context=texto_extraido)
            return {
                "answer": answer["answer"],
                "score": round(answer["score"], 2)
            }
        else:
            summary = self.summarizer(texto_extraido, max_length=120, min_length=30, do_sample=False)[0]['summary_text']
            return {
                "summary": summary
            }

    def extract_text(self, conteudo_bytes: bytes, filename: str) -> str:
        extracted_text = ""
        if filename.lower().endswith(".pdf"):
            imagens = convert_from_bytes(conteudo_bytes)
            for pagina in imagens:
                with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_img:
                    pagina.save(temp_img.name, "JPEG")
                    extracted_text += " ".join(self.reader.readtext(temp_img.name, detail=0)) + " "
                    os.remove(temp_img.name)
        else:
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_img:
                temp_img.write(conteudo_bytes)
                temp_img.flush()
                extracted_text = " ".join(self.reader.readtext(temp_img.name, detail=0))
                os.remove(temp_img.name)
        return extracted_text
