from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from uuid import UUID


# Criar instância do FastAPI
app = FastAPI(
    title="API TechMatch",
    description="Leitura inteligente de leitura de documentos",
    version="1.0.0"
)

# Modelos Pydantic
class Item(BaseModel):
    request_id: UUID = Form(...) # UUID
    listFiles: List[UploadFile] = File(...)
    query: Optional[str] = Form(None) # Prompt para ser processado
    user_id: str = Form(...) # Identificador do solicitante


class ItemResponse(BaseModel):
    query: str = Form(None) # Prompt para ser processado
    candidates: str = Form(None) # Melhores curriculos que se enquadram na vaga
    explainAbout: str = Form(None) # Justificativa sobre o prompt ou resumo de cada curriculo

# Banco de dados simulado
items_db = []
next_id = 1

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
def create_item(item: Item):
    """Recebe multiplos documentos como PDFs ou Imagens (JPEG/PNG)"""
    global next_id
    
    new_item = item.dict()
    new_item["id"] = next_id
    items_db.append(new_item)
    next_id += 1
    
    return new_item

@app.get("/items/", response_model=List[ItemResponse], tags=["Items"])
def read_items(skip: int = 0, limit: int = 10):
    """Listar todos os items com paginação"""
    return items_db[skip: skip + limit]

@app.get("/items/{item_id}", response_model=ItemResponse, tags=["Items"])
def read_item(item_id: int):
    """Buscar um item específico por ID"""
    for item in items_db:
        if item["id"] == item_id:
            return item
    raise HTTPException(status_code=404, detail="Item não encontrado")

@app.put("/items/{item_id}", response_model=ItemResponse, tags=["Items"])
def update_item(item_id: int, item: Item):
    """Atualizar um item existente"""
    for i, existing_item in enumerate(items_db):
        if existing_item["id"] == item_id:
            updated_item = item.dict()
            updated_item["id"] = item_id
            items_db[i] = updated_item
            return updated_item
    raise HTTPException(status_code=404, detail="Item não encontrado")

@app.delete("/items/{item_id}", tags=["Items"])
def delete_item(item_id: int):
    """Deletar um item"""
    for i, item in enumerate(items_db):
        if item["id"] == item_id:
            deleted_item = items_db.pop(i)
            return {"message": f"Item {item_id} deletado com sucesso", "deleted_item": deleted_item}
    raise HTTPException(status_code=404, detail="Item não encontrado")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)