# 🏠 Sistema de Scraping de Leilões

API desenvolvida com FastAPI para realizar scraping de leilões extrajudiciais.

## 📦 Instalação

```bash
# Clone o repositório
git clone <url-do-repo>
cd leiloes

# Instale as dependências
pip install -r requirements.txt
```

## 🚀 Como executar

### Iniciar a API

```bash
uvicorn main:app --reload
```

A API estará disponível em: `http://localhost:8000`

### Documentação Automática

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🔗 Endpoints

### `GET /`

Informações gerais da API

```json
{
  "message": "🏠 Sistema de Scraping de Leilões",
  "version": "1.0.0",
  "endpoints": {
    "scraping_vip": "/scraping/vip",
    "status": "/status",
    "pdfs": "/pdfs"
  }
}
```

### `POST /scraping/vip`

Executa o scraping do LeilaoVip

```json
{
  "status": "sucesso",
  "message": "Scraping concluído com sucesso!",
  "timestamp": "2025-10-22T10:30:00",
  "total_pdfs": 5,
  "pdfs_baixados": ["pdfs/bradesco_12345.pdf", "..."]
}
```

### `GET /status`

Verifica o status da aplicação

```json
{
  "status": "online",
  "timestamp": "2025-10-22T10:30:00",
  "message": "API funcionando normalmente"
}
```

### `GET /pdfs`

Lista todos os PDFs baixados

```json
{
  "status": "sucesso",
  "total": 3,
  "pdfs": [
    {
      "nome": "bradesco_12345.pdf",
      "caminho": "pdfs/bradesco_12345.pdf",
      "tamanho_bytes": 1024000,
      "data_criacao": "2025-10-22T10:15:30"
    }
  ]
}
```

## 🧪 Testes

Execute o script de testes:

```bash
python test_api.py
```

## 📁 Estrutura do Projeto

```
leiloes/
├── main.py              # API FastAPI
├── scrapping/
│   └── vip.py           # Scraper do LeilaoVip
├── pdfs/                # PDFs baixados
├── test_api.py          # Testes da API
└── README.md            # Este arquivo
```

## 🔧 Configurações

### Bancos suportados:

- **Bradesco**
- **Banco Pan**
- **BV**

### Palavra-chave de filtro:

- **"Extrajudicial"** - Apenas leilões que contenham esta palavra

## 💡 Exemplos de Uso

### cURL

```bash
# Verificar status
curl http://localhost:8000/status

# Executar scraping
curl -X POST http://localhost:8000/scraping/vip

# Listar PDFs
curl http://localhost:8000/pdfs
```

### Python

```python
import requests

# Executar scraping
response = requests.post("http://localhost:8000/scraping/vip")
result = response.json()
print(f"PDFs baixados: {result['total_pdfs']}")
```

## ⚠️ Observações

- O scraping respeita rate limits para não sobrecarregar os servidores
- Apenas leilões com a palavra "Extrajudicial" são processados
- Os PDFs são salvos na pasta `pdfs/`
- A API possui logs detalhados para acompanhamento

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request
