from pymongo import MongoClient
from datetime import datetime
from uuid import UUID
from typing import List, Optional, Dict


class DataBaseConnection:
    def __init__(self, uri="mongodb://localhost:27017/", nome_banco="logs_curriculos", nome_colecao="executions"):
        self.cliente = MongoClient(uri)
        self.banco = self.cliente[nome_banco]
        self.colecao = self.banco[nome_colecao]


    def insert(self, dados):
        self.colecao.insert_one(dados)

    def getAll(self):
        return list(self.colecao.find())