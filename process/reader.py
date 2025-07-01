import os
import logging
import tempfile
from typing import List, Optional, Tuple
from fastapi import UploadFile
import fitz  # PyMuPDF
from PIL import Image
import io
import asyncio
from concurrent.futures import ThreadPoolExecutor
import easyocr
import cv2
import numpy as np

from db.schema import ProcessedDocument, DocumentType

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Processador de documentos com OCR"""
    
    def __init__(self):
        # Inicializar EasyOCR
        self.ocr_reader = None
        self.executor = ThreadPoolExecutor(max_workers=4)
        self._init_ocr()
    
    def _init_ocr(self):
        """Inicializar EasyOCR com configurações otimizadas"""
        try:
            # Usar português e inglês
            self.ocr_reader = easyocr.Reader(['pt', 'en'], gpu=True)
            logger.info("EasyOCR inicializado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao inicializar EasyOCR: {e}")
            raise Exception(f"Falha na inicialização do OCR: {e}")
    
    async def process_documents(self, files: List[UploadFile]) -> List[ProcessedDocument]:
        """Processar lista de documentos"""
        processed_docs = []
        
        # Processar documentos em paralelo
        tasks = [self._process_single_document(file) for file in files]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Erro ao processar documento: {result}")
                continue
            
            if result:
                processed_docs.append(result)
        
        logger.info(f"Processados {len(processed_docs)} de {len(files)} documentos")
        return processed_docs
    
    async def _process_single_document(self, file: UploadFile) -> Optional[ProcessedDocument]:
        """Processar um documento individual"""
        try:
            # Ler conteúdo do arquivo
            content = await file.read()
            
            # Determinar tipo de documento
            doc_type = self._get_document_type(file.content_type)
            
            if doc_type == DocumentType.PDF:
                return await self._process_pdf(content, file.filename)
            elif doc_type == DocumentType.IMAGE:
                return await self._process_image(content, file.filename)
            else:
                logger.warning(f"Tipo não suportado: {file.content_type}")
                return None
                
        except Exception as e:
            logger.error(f"Erro ao processar {file.filename}: {e}")
            return None
    
    def _get_document_type(self, content_type: str) -> Optional[DocumentType]:
        """Determinar tipo de documento baseado no content-type"""
        if content_type == 'application/pdf':
            return DocumentType.PDF
        elif content_type in ['image/jpeg', 'image/jpg', 'image/png']:
            return DocumentType.IMAGE
        return None
    
    async def _process_pdf(self, content: bytes, filename: str) -> Optional[ProcessedDocument]:
        """Processar arquivo PDF"""
        try:
            # Usar thread pool para operações I/O intensivas
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor, 
                self._extract_pdf_text, 
                content
            )
            
            text, page_count, confidence = result
            
            if text.strip():
                return ProcessedDocument(
                    filename=filename,
                    content=text,
                    document_type=DocumentType.PDF,
                    confidence=confidence,
                    page_count=page_count
                )
            else:
                logger.warning(f"Nenhum texto extraído do PDF: {filename}")
                return None
                
        except Exception as e:
            logger.error(f"Erro ao processar PDF {filename}: {e}")
            return None
    
    def _extract_pdf_text(self, content: bytes) -> Tuple[str, int, float]:
        """Extrair texto de PDF usando PyMuPDF e OCR"""
        text_parts = []
        page_count = 0
        total_confidence = 0.0
        confidence_count = 0
        
        try:
            # Abrir PDF da memória
            pdf_document = fitz.open(stream=content, filetype="pdf")
            page_count = len(pdf_document)
            
            for page_num in range(page_count):
                page = pdf_document[page_num]
                
                # Tentar extrair texto diretamente
                page_text = page.get_text()
                
                if page_text.strip():
                    # Texto extraído diretamente
                    text_parts.append(page_text)
                    total_confidence += 0.95  # Alta confiança para texto direto
                    confidence_count += 1
                else:
                    # Usar OCR na página como imagem
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom
                    img_data = pix.tobytes("png")
                    
                    # Aplicar OCR
                    ocr_text, conf = self._apply_ocr_to_image_bytes(img_data)
                    if ocr_text.strip():
                        text_parts.append(ocr_text)
                        total_confidence += conf
                        confidence_count += 1
            
            pdf_document.close()
            
            # Calcular confiança média
            avg_confidence = total_confidence / confidence_count if confidence_count > 0 else 0.0
            
            return '\n\n'.join(text_parts), page_count, avg_confidence
            
        except Exception as e:
            logger.error(f"Erro na extração de texto do PDF: {e}")
            return "", 0, 0.0
    
    async def _process_image(self, content: bytes, filename: str) -> Optional[ProcessedDocument]:
        """Processar arquivo de imagem"""
        try:
            # Usar thread pool para OCR
            loop = asyncio.get_event_loop()
            text, confidence = await loop.run_in_executor(
                self.executor,
                self._apply_ocr_to_image_bytes,
                content
            )
            
            if text.strip():
                return ProcessedDocument(
                    filename=filename,
                    content=text,
                    document_type=DocumentType.IMAGE,
                    confidence=confidence,
                    page_count=1
                )
            else:
                logger.warning(f"Nenhum texto extraído da imagem: {filename}")
                return None
                
        except Exception as e:
            logger.error(f"Erro ao processar imagem {filename}: {e}")
            return None
    
    def _apply_ocr_to_image_bytes(self, image_bytes: bytes) -> Tuple[str, float]:
        """Aplicar OCR em bytes de imagem"""
        try:
            # Converter bytes para array numpy
            nparr = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                logger.error("Não foi possível decodificar a imagem")
                return "", 0.0
            
            # Pré-processamento da imagem para melhorar OCR
            processed_image = self._preprocess_image(image)
            
            # Aplicar OCR
            results = self.ocr_reader.readtext(processed_image, detail=1)
            
            # Extrair texto e calcular confiança média
            text_parts = []
            confidences = []
            
            for (bbox, text, confidence) in results:
                if confidence > 0.3:  # Filtrar resultados de baixa confiança
                    text_parts.append(text)
                    confidences.append(confidence)
            
            # Calcular confiança média
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            # Juntar texto
            full_text = ' '.join(text_parts)
            
            return full_text, avg_confidence
            
        except Exception as e:
            logger.error(f"Erro no OCR: {e}")
            return "", 0.0
    
    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Pré-processar imagem para melhorar OCR"""
        try:
            # Converter para escala de cinza
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # Redimensionar se muito pequena
            height, width = gray.shape
            if height < 300 or width < 300:
                scale_factor = max(300/height, 300/width)
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                gray = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
            
            # Aplicar filtro de desfoque gaussiano para reduzir ruído
            gray = cv2.GaussianBlur(gray, (3, 3), 0)
            
            # Aplicar threshold adaptativo
            processed = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            # Operação morfológica para melhorar a qualidade do texto
            kernel = np.ones((1, 1), np.uint8)
            processed = cv2.morphologyEx(processed, cv2.MORPH_CLOSE, kernel)
            
            return processed
            
        except Exception as e:
            logger.error(f"Erro no pré-processamento: {e}")
            return image
    
    def _clean_extracted_text(self, text: str) -> str:
        """Limpar e normalizar texto extraído"""
        if not text:
            return ""
        
        # Remover caracteres especiais desnecessários
        import re
        
        # Normalizar espaços em branco
        text = re.sub(r'\s+', ' ', text)
        
        # Remover caracteres não imprimíveis
        text = ''.join(char for char in text if char.isprintable() or char.isspace())
        
        # Remover linhas muito curtas (provavelmente ruído)
        lines = text.split('\n')
        cleaned_lines = [line.strip() for line in lines if len(line.strip()) > 2]
        
        return '\n'.join(cleaned_lines).strip()
    
    async def extract_text_preview(self, file: UploadFile, max_chars: int = 500) -> str:
        """Extrair preview do texto para validação rápida"""
        try:
            doc = await self._process_single_document(file)
            if doc and doc.content:
                preview = doc.content[:max_chars]
                if len(doc.content) > max_chars:
                    preview += "..."
                return preview
            return "Não foi possível extrair texto"
            
        except Exception as e:
            logger.error(f"Erro ao gerar preview: {e}")
            return f"Erro na extração: {str(e)}"
    
    def get_supported_formats(self) -> List[str]:
        """Retornar lista de formatos suportados"""
        return [
            "application/pdf",
            "image/jpeg",
            "image/jpg", 
            "image/png"
        ]
    
    async def validate_file(self, file: UploadFile) -> Tuple[bool, str]:
        """Validar se arquivo é suportado"""
        try:
            # Verificar tipo de conteúdo
            if file.content_type not in self.get_supported_formats():
                return False, f"Tipo não suportado: {file.content_type}"
            
            # Verificar tamanho (máximo 10MB)
            content = await file.read()
            await file.seek(0)  # Resetar posição do arquivo
            
            if len(content) > 10 * 1024 * 1024:  # 10MB
                return False, "Arquivo muito grande (máximo 10MB)"
            
            if len(content) == 0:
                return False, "Arquivo vazio"
            
            return True, "Arquivo válido"
            
        except Exception as e:
            return False, f"Erro na validação: {str(e)}"