# Glam Pro Beauty Assistant – Backend

A local-first AI beauty chatbot backend built with **FastAPI**, **Llama 3.2-3B** (GGUF via `llama-cpp-python`), and **ChromaDB** RAG. No external API calls – runs entirely on your machine.

---

## Features

| Feature | Detail |
|---|---|
| **Local LLM** | Llama 3.2-3B Instruct Q4_K_M – CPU or CUDA |
| **RAG** | Dual ChromaDB collections: products + app help |
| **Multilingual** | Arabic & English via multilingual embeddings |
| **Sponsored Boost** | Sponsored products boosted ×1.2 in retrieval scoring |
| **Session Memory** | Last 6 exchanges (12 messages) per session |
| **Admin API** | Hot-swap product & help data via JSON upload |
| **Health Check** | `/health` endpoint with LLM + collection status |

---

## Prerequisites

- Python 3.11+
- ~4 GB RAM free (for the quantised model)
- Optional: NVIDIA GPU with CUDA for faster inference

---

## Setup

### 1. Clone and create a virtual environment

```bash
git clone <your-repo-url>
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
```

### 2. Install dependencies

**CPU-only (default):**
```bash
pip install -r requirements.txt
```

**With NVIDIA CUDA acceleration:**
```bash
CMAKE_ARGS="-DLLAMA_CUDA=on" pip install llama-cpp-python --force-reinstall --no-cache-dir
pip install -r requirements.txt
```

**With Apple Silicon (Metal):**
```bash
CMAKE_ARGS="-DLLAMA_METAL=on" pip install llama-cpp-python --force-reinstall --no-cache-dir
pip install -r requirements.txt
```

### 3. Download the LLM model

```bash
mkdir models
# Install huggingface_hub if needed: pip install huggingface_hub
python -c "
from huggingface_hub import hf_hub_download
hf_hub_download(
    repo_id='bartowski/Llama-3.2-3B-Instruct-GGUF',
    filename='Llama-3.2-3B-Instruct-Q4_K_M.gguf',
    local_dir='./models'
)
print('Model downloaded!')
"
```

> Alternatively, download manually from:  
> https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF

### 4. Configure environment variables

```bash
cp .env.example .env
# Edit .env and set at minimum:
#   MODEL_PATH=./models/Llama-3.2-3B-Instruct-Q4_K_M.gguf
#   ADMIN_API_KEY=your-secret-key
```

### 5. Run the server

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The API is now available at `http://localhost:8000`.  
Interactive docs: `http://localhost:8000/docs`

---

## API Reference

### Health Check
```
GET /health
```
Returns LLM status and collection sizes. No authentication required.

### Session Management
```
GET /session/new
```
Returns a new UUID session ID for a conversation.

### Chat
```
POST /chat
Content-Type: application/json

{
  "session_id": "uuid-from-session-new",
  "message": "What moisturiser is good for dry skin?"
}
```
Returns:
```json
{
  "reply": "For dry skin, I'd recommend...",
  "session_id": "uuid-from-session-new"
}
```

### Admin: Upload Products
```
POST /admin/upload/products
X-API-Key: your-secret-key
Content-Type: multipart/form-data

file: <products.json>
```
Re-indexes the products ChromaDB collection. No server restart needed.

### Admin: Upload Help
```
POST /admin/upload/help
X-API-Key: your-secret-key
Content-Type: multipart/form-data

file: <app_help.json>
```

---

## Docker

```bash
# Build
docker build -t glam-pro-backend .

# Run (mount your models directory)
docker run -p 8000:8000 \
  -v $(pwd)/models:/app/models \
  -v $(pwd)/chroma_data:/app/chroma_data \
  -e ADMIN_API_KEY=your-secret \
  glam-pro-backend
```

---

## Data Formats

### products.json
```json
[
  {
    "id": "prod-001",
    "name": "Product Name",
    "brand": "Brand",
    "category": "skincare",
    "description": "...",
    "benefits": ["hydration", "glow"],
    "usage": "Apply ...",
    "sponsored": true,
    "price": 29.99,
    "currency": "USD"
  }
]
```

### app_help.json
```json
[
  {
    "id": "help-001",
    "question": "How do I ...?",
    "answer": "Step 1: ... Step 2: ...",
    "keywords": ["subscription", "plan"]
  }
]
```

---

## Project Structure

```
backend/
├── main.py          # FastAPI app & endpoints
├── rag.py           # ChromaDB RAG pipeline
├── llm.py           # Llama GGUF wrapper
├── memory.py        # Session conversation memory
├── prompt.py        # LLM prompt builder
├── models.py        # Pydantic schemas
├── requirements.txt
├── .env.example
├── Dockerfile
└── data/
    ├── products.json
    └── app_help.json
```
