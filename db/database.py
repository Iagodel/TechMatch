from pymongo import MongoClient
from datetime import datetime
import uuid

# Conectando ao MongoDB (ajuste a URL se usar MongoDB Atlas)
client = MongoClient("mongodb://localhost:27017/")

# Selecionando o banco e a coleção
db = client["logs_curriculos"]
colecao = db["executions"]

# Criando um log de teste
log = {
    "request_id": str(uuid.uuid4()),
    "user_id": "fabio01",
    "timestamp": datetime.utcnow().isoformat(),
    "query": "Engenheiro de Software com Python e Docker",
    "resultado": [
        {"arquivo": "curriculo_1.pdf", "score": 0.92},
        {"arquivo": "curriculo_3.pdf", "score": 0.89}
    ]
}

# Inserindo no Mongo
insert_result = colecao.insert_one(log)
print(f"\n✅ Log inserido com _id: {insert_result.inserted_id}")

# Buscando todos os logs
print("\n📋 Logs armazenados no banco:\n")
for doc in colecao.find():
    print(doc)