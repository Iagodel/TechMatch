from pymongo import MongoClient
from datetime import datetime
from uuid import UUID
from typing import List, Optional, Dict
import os


class DataBaseConnection:
    def __init__(self, uri: Optional[str] = None, nome_banco="logs_curriculos", nome_colecao="executions"):
        self.uri = uri or os.getenv("MONGO_URI", "mongodb://localhost:27017/")
        self.cliente = MongoClient(self.uri)
        self.banco = self.cliente[nome_banco]
        self.colecao = self.banco[nome_colecao]

    def insert(self, dados):
        self.colecao.insert_one(dados)

    def getAll(self):
        return list(self.colecao.find())