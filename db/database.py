import os
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import asyncio

from db.schema import LogEntry

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Gerenciador de banco de dados MongoDB"""
    
    def __init__(self):
        # Configurações do MongoDB
        self.mongodb_url = os.getenv("MONGODB_URL", "mongodb://mongo:27017")
        self.database_name = os.getenv("DATABASE_NAME", "logs_curriculos")
        self.collection_name = "executions"
        
        self.client: Optional[AsyncIOMotorClient] = None
        self.database = None
        self.collection = None
        
    async def connect(self):
        """Estabelecer conexão com MongoDB"""
        try:
            logger.info(f"Conectando ao MongoDB: {self.mongodb_url}")
            
            self.client = AsyncIOMotorClient(
                self.mongodb_url,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000,
                socketTimeoutMS=10000,
                maxPoolSize=50,
                retryWrites=True
            )
            
            # Testar conexão
            await self.client.admin.command('ping')
            
            self.database = self.client[self.database_name]
            self.collection = self.database[self.collection_name]
            
            # Criar índices para otimização
            await self._create_indexes()
            
            logger.info("Conexão com MongoDB estabelecida com sucesso")
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Erro ao conectar com MongoDB: {e}")
            raise Exception(f"Falha na conexão com banco de dados: {e}")
        except Exception as e:
            logger.error(f"Erro inesperado ao conectar: {e}")
            raise
    
    async def disconnect(self):
        """Fechar conexão com MongoDB"""
        if self.client:
            logger.info("Fechando conexão com MongoDB")
            self.client.close()
    
    async def _create_indexes(self):
        """Criar índices para otimizar consultas"""
        try:
            # Índice no request_id (único)
            await self.collection.create_index("request_id", unique=True)
            
            # Índice no user_id para consultas por usuário
            await self.collection.create_index("user_id")
            
            # Índice no timestamp para consultas temporais
            await self.collection.create_index("timestamp")
            
            # Índice composto para consultas user_id + timestamp
            await self.collection.create_index([
                ("user_id", 1),
                ("timestamp", -1)
            ])
            
            logger.info("Índices criados com sucesso")
            
        except Exception as e:
            logger.warning(f"Erro ao criar índices: {e}")
    
    async def save_log(self, log_entry: LogEntry) -> bool:
        """Salvar entrada de log no banco"""
        try:
            # Converter para dict
            log_dict = log_entry.dict()

            # Sanitizar o campo 'result'
            def sanitize_result(result: Any) -> Any:
                if isinstance(result, dict):
                    sanitized = {}
                    for k, v in result.items():
                        if k in ("results", "summaries"):
                            # Lista de documentos — remover campos sensíveis
                            sanitized[k] = [
                                {kk: vv for kk, vv in item.items() if kk not in ("content", "content_preview", "summary")}
                                for item in v if isinstance(item, dict)
                            ]
                        elif isinstance(v, dict):
                            sanitized[k] = sanitize_result(v)
                        else:
                            sanitized[k] = v
                    return sanitized
                return result

            log_dict["result"] = sanitize_result(log_dict["result"])

            # Garantir timestamp
            if isinstance(log_dict["timestamp"], str):
                log_dict["timestamp"] = datetime.fromisoformat(log_dict["timestamp"])

            result = await self.collection.insert_one(log_dict)

            if result.inserted_id:
                logger.info(f"Log salvo com sucesso: {log_entry.request_id}")
                return True
            else:
                logger.error(f"Falha ao salvar log: {log_entry.request_id}")
                return False

        except Exception as e:
            logger.error(f"Erro ao salvar log: {e}")
            return False

    
    async def get_log(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Buscar log por request_id"""
        try:
            log = await self.collection.find_one({"request_id": request_id})
            
            if log:
                # Converter ObjectId para string
                log['_id'] = str(log['_id'])
                logger.info(f"Log encontrado: {request_id}")
                return log
            else:
                logger.info(f"Log não encontrado: {request_id}")
                return None
                
        except Exception as e:
            logger.error(f"Erro ao buscar log: {e}")
            return None
    
    async def get_user_logs(self, user_id: str, limit: int = 50, skip: int = 0) -> List[Dict[str, Any]]:
        """Buscar logs de um usuário específico"""
        try:
            cursor = self.collection.find(
                {"user_id": user_id}
            ).sort("timestamp", -1).limit(limit).skip(skip)
            
            logs = []
            async for log in cursor:
                log['_id'] = str(log['_id'])
                logs.append(log)
            
            logger.info(f"Encontrados {len(logs)} logs para usuário: {user_id}")
            return logs
            
        except Exception as e:
            logger.error(f"Erro ao buscar logs do usuário: {e}")
            return []
    
    async def get_logs_by_date_range(
        self, 
        start_date: datetime, 
        end_date: datetime,
        user_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Buscar logs por intervalo de datas"""
        try:
            query = {
                "timestamp": {
                    "$gte": start_date,
                    "$lte": end_date
                }
            }
            
            if user_id:
                query["user_id"] = user_id
            
            cursor = self.collection.find(query).sort("timestamp", -1).limit(limit)
            
            logs = []
            async for log in cursor:
                log['_id'] = str(log['_id'])
                logs.append(log)
            
            logger.info(f"Encontrados {len(logs)} logs no período especificado")
            return logs
            
        except Exception as e:
            logger.error(f"Erro ao buscar logs por data: {e}")
            return []
    
    async def get_usage_stats(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Obter estatísticas de uso"""
        try:
            pipeline = []
            
            # Filtrar por usuário se especificado
            if user_id:
                pipeline.append({"$match": {"user_id": user_id}})
            
            # Agregação para estatísticas
            pipeline.extend([
                {
                    "$group": {
                        "_id": None,
                        "total_requests": {"$sum": 1},
                        "total_documents": {"$sum": "$documents_count"},
                        "unique_users": {"$addToSet": "$user_id"},
                        "queries_with_text": {
                            "$sum": {
                                "$cond": [{"$ne": ["$query", None]}, 1, 0]
                            }
                        },
                        "queries_summary_only": {
                            "$sum": {
                                "$cond": [{"$eq": ["$query", None]}, 1, 0]
                            }
                        }
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "total_requests": 1,
                        "total_documents": 1,
                        "unique_users_count": {"$size": "$unique_users"},
                        "queries_with_text": 1,
                        "queries_summary_only": 1,
                        "avg_documents_per_request": {
                            "$divide": ["$total_documents", "$total_requests"]
                        }
                    }
                }
            ])
            
            result = await self.collection.aggregate(pipeline).to_list(1)
            
            if result:
                stats = result[0]
                logger.info("Estatísticas de uso geradas")
                return stats
            else:
                return {
                    "total_requests": 0,
                    "total_documents": 0,
                    "unique_users_count": 0,
                    "queries_with_text": 0,
                    "queries_summary_only": 0,
                    "avg_documents_per_request": 0
                }
                
        except Exception as e:
            logger.error(f"Erro ao gerar estatísticas: {e}")
            return {}
    
    async def health_check(self) -> bool:
        """Verificar se a conexão com banco está funcionando"""
        try:
            if not self.client:
                return False
            
            # Ping no servidor
            await self.client.admin.command('ping')
            return True
            
        except Exception as e:
            logger.error(f"Health check falhou: {e}")
            return False
    
    async def cleanup_old_logs(self, days_to_keep: int = 90) -> int:
        """Limpar logs antigos (opcional para manutenção)"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            result = await self.collection.delete_many({
                "timestamp": {"$lt": cutoff_date}
            })
            
            deleted_count = result.deleted_count
            logger.info(f"Removidos {deleted_count} logs antigos")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Erro ao limpar logs antigos: {e}")
            return 0