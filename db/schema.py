from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class DocumentType(str, Enum):
    """Tipos de documento suportados"""
    PDF = "pdf"
    IMAGE = "image"

class ProcessedDocument(BaseModel):
    """Documento processado após OCR"""
    filename: str = Field(..., description="Nome do arquivo original")
    content: str = Field(..., description="Texto extraído do documento")
    document_type: DocumentType = Field(..., description="Tipo do documento")
    confidence: Optional[float] = Field(None, description="Confiança do OCR (0-1)")
    page_count: Optional[int] = Field(None, description="Número de páginas (para PDFs)")

class ProcessRequest(BaseModel):
    """Modelo para requisição de processamento"""
    files: List[str] = Field(..., description="Lista de nomes de arquivos")
    query: Optional[str] = Field(None, description="Pergunta sobre os currículos")
    request_id: Optional[str] = Field(None, description="ID único da requisição")
    user_id: str = Field(..., description="ID do usuário solicitante")

    class Config:
        schema_extra = {
            "example": {
                "files": ["curriculo1.pdf", "curriculo2.jpg"],
                "query": "Qual desses currículos se enquadra melhor para vaga de Python Developer?",
                "request_id": "12345678-1234-1234-1234-123456789012",
                "user_id": "fabio_ta"
            }
        }

class SummaryItem(BaseModel):
    """Item de sumário individual de currículo"""
    filename: str = Field(..., description="Nome do arquivo")
    summary: str = Field(..., description="Resumo do currículo")
    key_skills: List[str] = Field(default=[], description="Principais habilidades identificadas")
    experience_years: Optional[int] = Field(None, description="Anos de experiência estimados")
    education: Optional[str] = Field(None, description="Formação acadêmica principal")
    
    class Config:
        schema_extra = {
            "example": {
                "filename": "curriculo_joao.pdf",
                "summary": "Desenvolvedor Python com 5 anos de experiência em desenvolvimento web e APIs REST.",
                "key_skills": ["Python", "Django", "FastAPI", "PostgreSQL", "Docker"],
                "experience_years": 5,
                "education": "Bacharelado em Ciência da Computação"
            }
        }

class SummaryResponse(BaseModel):
    """Resposta com sumários individuais"""
    summaries: List[SummaryItem] = Field(..., description="Lista de sumários dos currículos")
    
    class Config:
        schema_extra = {
            "example": {
                "summaries": [
                    {
                        "filename": "curriculo_ana.pdf",
                        "summary": "Desenvolvedora Full Stack com expertise em React e Node.js",
                        "key_skills": ["JavaScript", "React", "Node.js", "MongoDB"],
                        "experience_years": 3,
                        "education": "Tecnólogo em Sistemas para Internet"
                    }
                ]
            }
        }

class QueryAnalysis(BaseModel):
    """Análise baseada em query específica"""
    query: str = Field(..., description="Pergunta analisada")
    best_matches: List[Dict[str, Any]] = Field(..., description="Melhores candidatos")
    analysis: str = Field(..., description="Análise detalhada")
    
    class Config:
        schema_extra = {
            "example": {
                "query": "Qual candidato tem mais experiência com Python?",
                "best_matches": [
                    {
                        "filename": "curriculo_carlos.pdf",
                        "score": 0.95,
                        "justification": "5+ anos de experiência com Python, Django e FastAPI"
                    }
                ],
                "analysis": "Carlos demonstra a maior experiência com Python, seguido por Ana..."
            }
        }

class ProcessResponse(BaseModel):
    """Resposta principal do processamento"""
    request_id: str = Field(..., description="ID único da requisição")
    user_id: str = Field(..., description="ID do usuário")
    timestamp: datetime = Field(..., description="Timestamp do processamento")
    #query: Optional[str] = Field(None, description="Query utilizada")
    result: Dict[str, Any] = Field(..., description="Resultado do processamento")
    #documents_processed: Optional[int] = Field(..., description="Número de documentos processados")
    #response_type: Optional[str] = Field(..., description="Tipo de resposta: 'summaries' ou 'query_analysis'")
    
    class Config:
        schema_extra = {
            "example": {
                "request_id": "12345678-1234-1234-1234-123456789012",
                "user_id": "fabio_ta",
                "timestamp": "2025-07-01T10:30:00Z",
                "query": "Qual candidato tem experiência com Docker?",
                "result": {
                    "best_matches": [
                        {
                            "filename": "curriculo_pedro.pdf",
                            "score": 0.88,
                            "justification": "Experiência com Docker, Kubernetes e CI/CD"
                        }
                    ]
                },
                "documents_processed": 3,
                "response_type": "query_analysis"
            }
        }

class LogEntry(BaseModel):
    """Entrada de log no banco de dados"""
    request_id: str = Field(..., description="ID único da requisição")
    user_id: str = Field(..., description="ID do usuário")
    timestamp: datetime = Field(..., description="Timestamp da requisição")
    query: Optional[str] = Field(None, description="Query utilizada")
    result: Dict[str, Any] = Field(..., description="Resultado obtido")
    documents_count: int = Field(..., description="Número de documentos processados")
    
    class Config:
        schema_extra = {
            "example": {
                "request_id": "12345678-1234-1234-1234-123456789012",
                "user_id": "fabio_ta",
                "timestamp": "2025-07-01T10:30:00Z",
                "query": "Desenvolvedores Python sênior",
                "result": {"analysis": "Encontrados 2 candidatos..."},
                "documents_count": 5
            }
        }

class ErrorResponse(BaseModel):
    """Modelo para respostas de erro"""
    error: str = Field(..., description="Mensagem de erro")
    detail: Optional[str] = Field(None, description="Detalhes adicionais do erro")
    request_id: Optional[str] = Field(None, description="ID da requisição que falhou")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp do erro")
    
    class Config:
        schema_extra = {
            "example": {
                "error": "Tipo de arquivo não suportado",
                "detail": "Apenas PDF, JPEG e PNG são aceitos",
                "request_id": "12345678-1234-1234-1234-123456789012",
                "timestamp": "2025-07-01T10:30:00Z"
            }
        }

class HealthResponse(BaseModel):
    """Resposta do health check"""
    status: str = Field(..., description="Status da aplicação")
    timestamp: datetime = Field(..., description="Timestamp da verificação")
    database: str = Field(..., description="Status da conexão com banco")
    version: str = Field(..., description="Versão da aplicação")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2025-07-01T10:30:00Z",
                "database": "connected",
                "version": "1.0.0"
            }
        }