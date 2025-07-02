import logging
from typing import List, Dict, Any, Optional
import asyncio
from transformers import pipeline
import re

from db.schema import ProcessedDocument, SummaryItem

logger = logging.getLogger(__name__)

class PromptManager:
    """Gerenciador com LLM para interpretação contextual"""
    
    def __init__(self):
        self.llm = None
        self._initialize_llm()
    
    def _initialize_llm(self):
        """Inicializar LLM para análise contextual"""
        try:
            logger.info("Inicializando LLM para análise contextual...")

            self.llm = pipeline(
                "text-generation",
                model="tiiuae/falcon-rw-1b ",
                tokenizer="tiiuae/falcon-rw-1b ",
                device=0,
                max_length=1024*20,
                do_sample=True,
                temperature=0.3,
                pad_token_id=50256
            )

            logger.info("LLM inicializada com sucesso")
        except Exception as e:
            logger.error(f"Erro ao inicializar LLM: {e}")
            self.llm = None
            logger.warning("LLM indisponível - usando análise básica")

    async def process_documents(self, documents: List[ProcessedDocument], query: Optional[str] = None) -> Dict[str, Any]:
        try:
            if query and query.strip():
                return await self._analyze_with_llm(documents, query.strip())
            else:
                return await self._summarize_with_llm(documents)
        except Exception as e:
            logger.error(f"Erro no processamento: {e}")
            return {"error": f"Erro no processamento: {str(e)}", "documents_processed": 0}

    async def _analyze_with_llm(self, documents: List[ProcessedDocument], query: str) -> Dict[str, Any]:
        try:
            results = []
            for doc in documents:
                analysis = await self._analyze_single_document(doc, query)
                if analysis:
                    results.append(analysis)
            consolidated_analysis = await self._generate_consolidated_analysis(query, results)
            return {
                "query": query,
                "type": "llm_analysis",
                "results": results,
                "consolidated_analysis": consolidated_analysis,
                "total_documents": len(documents),
                "analyzed_documents": len(results)
            }
        except Exception as e:
            logger.error(f"Erro na análise com LLM: {e}")
            return {"error": str(e), "results": []}

    async def _summarize_with_llm(self, documents: List[ProcessedDocument]) -> Dict[str, Any]:
        try:
            summaries = []
            for doc in documents:
                summary = await self._generate_smart_summary(doc)
                if summary:
                    summaries.append(summary)
            general_analysis = await self._generate_general_analysis(summaries)
            return {
                "type": "llm_summaries",
                "summaries": summaries,
                "general_analysis": general_analysis,
                "total_documents": len(documents)
            }
        except Exception as e:
            logger.error(f"Erro na geração de resumos: {e}")
            return {"error": str(e), "summaries": []}

    async def _analyze_single_document(self, doc: ProcessedDocument, query: str) -> Optional[Dict[str, Any]]:
        try:
            content_preview = self._prepare_content_for_llm(doc.content)
            prompt = self._create_analysis_prompt(query, content_preview)
            if self.llm:
                analysis_result = await self._run_llm_analysis(prompt)
            else:
                analysis_result = self._basic_analysis_fallback(doc.content, query)
            return {
                "filename": doc.filename,
                "document_type": doc.document_type.value,
                "confidence": round(doc.confidence, 2),
                "analysis": analysis_result,
                "content_preview": content_preview[:200] + "..." if len(content_preview) > 200000 else content_preview
            }
        except Exception as e:
            logger.error(f"Erro ao analisar {doc.filename}: {e}")
            return None

    async def _generate_smart_summary(self, doc: ProcessedDocument) -> Optional[Dict[str, Any]]:
        try:
            content_preview = self._prepare_content_for_llm(doc.content)
            prompt = f"""[INSTRUÇÃO]
Resuma o seguinte currículo profissional de forma estruturada e em português.

[CURRÍCULO]
{content_preview}

[RESUMO]"""
            if self.llm:
                summary_text = await self._run_llm_generation(prompt)
            else:
                summary_text = self._basic_summary_fallback(doc.content)
            return {
                "filename": doc.filename,
                "document_type": doc.document_type.value,
                "confidence": round(doc.confidence, 2),
                "summary": summary_text,
                "character_count": len(doc.content)
            }
        except Exception as e:
            logger.error(f"Erro ao resumir {doc.filename}: {e}")
            return None

    def _create_analysis_prompt(self, query: str, content: str) -> str:
        return f"""[INSTRUÇÃO]
Você é um especialista em análise de currículos

[PERGUNTA]
{query}

[CURRÍCULO]
{content}

[RESPOSTA]"""

    async def _run_llm_analysis(self, prompt: str) -> str:
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, lambda: self.llm(prompt, max_new_tokens=300, num_return_sequences=1))
            generated_text = result[0]['generated_text']
            analysis = generated_text.replace(prompt, "").strip()
            logger.debug(f"Texto gerado pela LLM: {generated_text}")
            return self._clean_llm_output(analysis)
        except Exception as e:
            logger.error(f"Erro na execução da LLM: {e}")
            return "Erro na análise com LLM"

    async def _run_llm_generation(self, prompt: str) -> str:
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, lambda: self.llm(prompt, max_new_tokens=300, num_return_sequences=1))
            generated_text = result[0]['generated_text']
            summary = generated_text.replace(prompt, "").strip()
            return self._clean_llm_output(summary)
        except Exception as e:
            logger.error(f"Erro na geração com LLM: {e}")
            return "Erro na geração de resumo"

    async def _generate_consolidated_analysis(self, query: str, results: List[Dict]) -> str:
        try:
            if not results:
                return f"Nenhum documento foi analisado para a consulta: '{query}'"
            analyses = [r.get('analysis', '') for r in results if r.get('analysis')]
            if self.llm and analyses:
                consolidation_prompt = f"""[INSTRUÇÃO]
Com base nas análises abaixo, gere uma resposta consolidada para a consulta: "{query}"

[ANÁLISES]
{chr(10).join([f"Documento {i+1}: {analysis}" for i, analysis in enumerate(analyses)])}

[ANÁLISE CONSOLIDADA]"""
                consolidated = await self._run_llm_generation(consolidation_prompt)
                return consolidated
            else:
                return f"Analisados {len(results)} documentos para '{query}'. Verifique os resultados individuais para detalhes."
        except Exception as e:
            logger.error(f"Erro na análise consolidada: {e}")
            return "Erro na geração da análise consolidada"

    async def _generate_general_analysis(self, summaries: List[Dict]) -> str:
        if not summaries:
            return "Nenhum resumo foi gerado"
        try:
            if self.llm:
                summaries_text = "\n".join([f"- {s.get('filename', 'Doc')}: {s.get('summary', '')[:100]}..." for s in summaries])
                general_prompt = f"""[INSTRUÇÃO]
Com base nos resumos abaixo, forneça uma análise geral do conjunto de currículos.

[RESUMOS]
{summaries_text}

[ANÁLISE GERAL]"""
                general_analysis = await self._run_llm_generation(general_prompt)
                return general_analysis
            else:
                return f"Processados {len(summaries)} documentos com resumos individuais gerados."
        except Exception as e:
            logger.error(f"Erro na análise geral: {e}")
            return "Erro na análise geral"

    def _prepare_content_for_llm(self, content: str, max_chars: int = 1500) -> str:
        if len(content) <= max_chars:
            return content
        truncated = content[:max_chars]
        last_space = truncated.rfind(' ')
        if last_space > max_chars * 0.8:
            truncated = truncated[:last_space]
        return truncated + "..."

    def _clean_llm_output(self, text: str) -> str:
        if not text:
            return "Análise não disponível"
        lines = text.split('\n')
        cleaned_lines = []
        seen_lines = set()
        for line in lines:
            line = line.strip()
            if line and line not in seen_lines and len(line) > 5:
                cleaned_lines.append(line)
                seen_lines.add(line)
        result = '\n'.join(cleaned_lines)
        #if len(result) > 500000:
        #    result = result[:500000] + "..."
        return result if result else "Análise não disponível"

    def _basic_analysis_fallback(self, content: str, query: str) -> str:
        content_lower = content.lower()
        query_lower = query.lower()
        query_words = re.findall(r'\b\w+\b', query_lower)
        query_words = [w for w in query_words if len(w) > 2]
        matches = [word for word in query_words if word in content_lower]
        if matches:
            return f"Documento relevante. Encontradas as seguintes correspondências: {', '.join(matches)}. Recomenda-se análise detalhada."
        else:
            return "Documento com baixa relevância para a consulta. Poucas correspondências encontradas."

    def _basic_summary_fallback(self, content: str) -> str:
        summary = content
        #if len(content) > 300:
        #    summary += "..."
        return f"Resumo básico: {summary}"
