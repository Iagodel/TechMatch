from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from typing import List, Optional
import uuid
from datetime import datetime
import logging
from contextlib import asynccontextmanager

from db.schema import ProcessRequest, ProcessResponse, SummaryResponse, LogEntry
from db.database import DatabaseManager
from process.reader import DocumentProcessor
from process.prompts import PromptManager

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializar componentes
db_manager = DatabaseManager()
doc_processor = DocumentProcessor()
prompt_manager = PromptManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerenciar ciclo de vida da aplicação"""
    # Startup
    logger.info("Inicializando aplicação...")
    await db_manager.connect()
    yield
    # Shutdown
    logger.info("Finalizando aplicação...")
    await db_manager.disconnect()

app = FastAPI(
    title="TechMatch CV Analyzer",
    description="API inteligente para análise de currículos usando OCR e LLM",
    version="1.0.0",
    lifespan=lifespan
)

@app.post(
    "/analyze-cvs",
    response_model=ProcessResponse,
    summary="Analisar currículos",
    description="Processa múltiplos currículos e responde perguntas específicas ou gera sumários"
)
async def analyze_cvs(
    files: List[UploadFile] = File(..., description="Lista de arquivos PDF ou imagens (JPEG/PNG)"),
    query: Optional[str] = Form(None, description="Pergunta específica sobre os currículos"),
    user_id: str = Form(..., description="ID do usuário solicitante")
):
    """
    Endpoint principal para análise de currículos.
    
    - **files**: Lista de arquivos (PDF, JPEG, PNG)
    - **query**: Pergunta opcional sobre os currículos
    - **request_id**: ID único da requisição (gerado automaticamente se não fornecido)
    - **user_id**: Identificador do usuário
    
    Se query não for fornecida, retorna sumários individuais de cada currículo.
    Se query for fornecida, retorna análise específica baseada na pergunta.
    """
    try:
        # Gerar request_id se não fornecido
        
        request_id = str(uuid.uuid4())
        
        # Validar tipos de arquivo
        allowed_types = {
            'application/pdf',
            'image/jpeg',
            'image/jpg', 
            'image/png'
        }
        
        for file in files:
            if file.content_type not in allowed_types:
                raise HTTPException(
                    status_code=400,
                    detail=f"Tipo de arquivo não suportado: {file.content_type}. "
                           f"Tipos aceitos: PDF, JPEG, PNG"
                )
        
        # Processar documentos
        logger.info(f"Processando {len(files)} arquivo(s) para request_id: {request_id}")
        processed_docs = await doc_processor.process_documents(files)
        
        if not processed_docs:
            raise HTTPException(
                status_code=400,
                detail="Não foi possível extrair texto de nenhum documento"
            )
        
       
        result = await prompt_manager.process_documents(processed_docs, query)
           
        
        # Preparar resposta
        response = ProcessResponse(
            request_id=request_id,
            user_id=user_id,
            timestamp=datetime.now(),
            result=result,
        )
        
        # Registrar log no banco
        log_entry = LogEntry(
            request_id=request_id,
            user_id=user_id,
            timestamp=datetime.utcnow(),
            query=query,
            result=result,
            documents_count=len(processed_docs)
        )
        
        await db_manager.save_log(log_entry)
        
        logger.info(f"Processamento concluído para request_id: {request_id}")
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro no processamento: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@app.get(
    "/logs/{request_id}",
    summary="Buscar log por ID",
    description="Recupera informações de log de uma requisição específica"
)
async def get_log(request_id: str):
    """Buscar log específico por request_id"""
    try:
        log = await db_manager.get_log(request_id)
        if not log:
            raise HTTPException(status_code=404, detail="Log não encontrado")
        return log
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar log: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@app.get(
    "/logs/user/{user_id}",
    summary="Buscar logs por usuário",
    description="Recupera histórico de logs de um usuário específico"
)
async def get_user_logs(user_id: str, limit: int = 50, skip: int = 0):
    """Buscar logs de um usuário específico"""
    try:
        logs = await db_manager.get_user_logs(user_id, limit, skip)
        return {
            "user_id": user_id,
            "logs": logs,
            "count": len(logs)
        }
    except Exception as e:
        logger.error(f"Erro ao buscar logs do usuário: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@app.get(
    "/health",
    summary="Health Check",
    description="Verifica se a API está funcionando corretamente"
)
async def health_check():
    """Health check endpoint"""
    try:
        # Verificar conexão com banco
        db_status = await db_manager.health_check()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow(),
            "database": "connected" if db_status else "disconnected",
            "version": "1.0.0"
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow()
            }
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)