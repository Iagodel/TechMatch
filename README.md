Projeto FastAPI com Swagger e Docker
Uma aplicação Python usando FastAPI com documentação automática Swagger e containerização Docker.

Funcionalidades
✅ API REST com FastAPI
✅ Documentação automática Swagger/OpenAPI
✅ Containerização com Docker
✅ Docker Compose para desenvolvimento
✅ CRUD completo para gerenciamento de items
✅ Validação de dados com Pydantic
✅ Health check endpoint
Estrutura do Projeto
projeto/
├── main.py              # Aplicação principal
├── requirements.txt     # Dependências Python
├── Dockerfile          # Configuração Docker
├── docker-compose.yml  # Orquestração Docker
├── .dockerignore      # Arquivos ignorados pelo Docker
└── README.md          # Este arquivo
Como Executar
Opção 1: Com Docker Compose (Recomendado)
bash
# Clonar/criar os arquivos do projeto
# Em seguida executar:
docker-compose up --build
Opção 2: Com Docker
bash
# Construir a imagem
docker build -t fastapi-app .

# Executar o container
docker run -d -p 8000:8000 fastapi-app
Opção 3: Ambiente Local
bash
# Instalar dependências
pip install -r requirements.txt

# Executar aplicação
python main.py
Acessar a Aplicação
Após executar, acesse:

API: http://localhost:8000
Documentação Swagger: http://localhost:8000/docs
Documentação ReDoc: http://localhost:8000/redoc
Health Check: http://localhost:8000/health
Endpoints Disponíveis
Gerais
GET / - Página inicial
GET /health - Verificação de saúde da API
Items (CRUD)
POST /items/ - Criar novo item
GET /items/ - Listar items (com paginação)
GET /items/{item_id} - Buscar item por ID
PUT /items/{item_id} - Atualizar item
DELETE /items/{item_id} - Deletar item
Exemplo de Uso
Criar um item:
bash
curl -X POST "http://localhost:8000/items/" \
     -H "Content-Type: application/json" \
     -d '{
       "nome": "Produto Exemplo",
       "descricao": "Descrição do produto",
       "preco": 29.99,
       "ativo": true
     }'
Listar items:
bash
curl "http://localhost:8000/items/"
Desenvolvimento
Para desenvolvimento local com hot-reload:

bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
Tecnologias Utilizadas
FastAPI: Framework web moderno e rápido
Pydantic: Validação de dados
Uvicorn: Servidor ASGI
Docker: Containerização
Docker Compose: Orquestração de containers
Próximos Passos
Você pode expandir este projeto adicionando:

Banco de dados (PostgreSQL, MySQL, SQLite)
Autenticação e autorização (JWT)
Testes automatizados (pytest)
Logging avançado
Middlewares personalizados
Cache (Redis)
Monitoramento e métricas
Contribuição
Faça um fork do projeto
Crie uma branch para sua feature
Commit suas mudanças
Push para a branch
Abra um Pull Request
