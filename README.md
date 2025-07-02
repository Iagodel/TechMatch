# 🧠 TechMatch CV Analyzer

Uma aplicação Python com FastAPI para **análise inteligente de currículos**, utilizando OCR, LLMs (como Falcon ou GPT-Neo) e banco de dados MongoDB para auditoria e histórico. A documentação é gerada automaticamente com Swagger.

---

## ✅ Funcionalidades

- 🔍 Extração de texto de PDFs e imagens via EasyOCR
- 🤖 Análise de currículos usando modelos de linguagem (LLM)
- 📄 Geração de resumos e respostas baseadas em queries personalizadas
- 📟 Armazenamento de logs e auditoria com MongoDB
- 🚀 API REST com FastAPI + Swagger
- 🐳 Containerização com Docker e orquestração com Docker Compose
- 💚 Endpoint de health check
- 📊 Endpoints para consulta de uso e histórico por usuário

---

## 📂 Estrutura do Projeto

```
projeto/
├── main.py               # API principal com FastAPI
├── process/
     ├── prompts.py            # Gerenciador de prompts e uso de LLMs
     ├── reader.py             # Processamento OCR e extração de texto
├── db/
     ├── database.py           # Gerenciador de conexão MongoDB
     ├── schema.py             # Schemas com Pydantic
├── requirements.txt      # Dependências
├── Dockerfile            # Build da imagem Docker
├── docker-compose.yml    # Orquestração de serviços
├── .dockerignore         # Exclusões do Docker
└── README.md             # Este arquivo
```

---

## 🚀 Como Executar

### 🔧 Opção 1: Docker Compose (recomendado)

```bash
docker-compose up --build
```

### 🐳 Opção 2: Docker puro

```bash
docker build -t cv-analyzer .
docker run -d -p 8000:8000 cv-analyzer
```

### 💻 Opção 3: Ambiente local (com Python)

```bash
pip install -r requirements.txt
python main.py
```

---

## 🌐 Acesso à Aplicação

- API: [http://localhost:8000](http://localhost:8000)
- Swagger (Docs): [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- Health Check: [http://localhost:8000/health](http://localhost:8000/health)

---

## 📬 Endpoints Disponíveis

### 🔹 Análise de Currículos

| Método | Rota           | Descrição                           |
| ------ | -------------- | ----------------------------------- |
| `POST` | `/analyze-cvs` | Faz análise ou resumo de currículos |

### 🔹 Logs e Auditoria

| Método | Rota                   | Descrição                                |
| ------ | ---------------------- | ---------------------------------------- |
| `GET`  | `/logs/{request_id}`   | Retorna log de uma requisição específica |
| `GET`  | `/logs/user/{user_id}` | Retorna logs por usuário                 |
| `GET`  | `/health`              | Verifica se a API está no ar             |

---

## 📈 Exemplo de Requisição

```bash
curl -X POST "http://localhost:8000/analyze-cvs" \
  -H "accept: application/json" \
  -F "files=@curriculo.pdf" \
  -F "query=Resuma o currículo" \
  -F "user_id=fabio123"
```

---

## 💪 Desenvolvimento

Para desenvolvimento local com reload automático:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

---

## 🛠 Tecnologias Utilizadas

- **FastAPI** — framework web moderno e rápido
- **EasyOCR** — extração de texto de imagens/PDFs
- **Transformers / HuggingFace** — modelos LLM
- **MongoDB** — persistência de logs e auditoria
- **Pydantic** — validação de dados
- **Uvicorn** — servidor ASGI
- **Docker & Docker Compose** — containerização

---

## 📊 Próximos Passos (Sugestões)

- Integração com Redis para cache de resultados
- Suporte a autenticação via OAuth2/JWT
- Painel administrativo para visualização de estatísticas
- Implementar testes com `pytest`
- Monitoramento com Prometheus + Grafana
- Melhoria de ambiente para LLMs mais robustas

