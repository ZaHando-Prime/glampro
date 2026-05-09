# Glam Pro Beauty Assistant

A fully local, production-ready AI beauty chatbot consisting of:

| Component | Tech | Location |
|---|---|---|
| **Backend API** | Python · FastAPI · Llama 3.2-3B · ChromaDB | `backend/` |
| **Flutter Widget** | Dart · Flutter 3.19+ · Provider | `glam_pro_chat/` |

---

## Quick Start

### 1. Run the Backend

```bash
cd backend

# Create virtual environment
python -m venv .venv && .venv\Scripts\activate   # Windows
# source .venv/bin/activate                       # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment variables
cp .env.example .env
# Edit .env: set MODEL_PATH and ADMIN_API_KEY

# (Optional) Download the LLM model
python -c "
from huggingface_hub import hf_hub_download
hf_hub_download(
    repo_id='bartowski/Llama-3.2-3B-Instruct-GGUF',
    filename='Llama-3.2-3B-Instruct-Q4_K_M.gguf',
    local_dir='./models'
)
"

# Start the API server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Backend is ready at **http://localhost:8000**  
API docs at **http://localhost:8000/docs**

---

### 2. Run the Flutter Example App

```bash
cd glam_pro_chat/example

# Install dependencies
flutter pub get

# Edit lib/main.dart → update _apiUrl to your machine's IP
# Android emulator: http://10.0.2.2:8000
# Physical device:  http://<your-LAN-IP>:8000

flutter run
```

---

## Project Structure

```
glam-pro-project/
│
├── backend/                   # Python FastAPI backend
│   ├── main.py                # API entry point
│   ├── rag.py                 # RAG pipeline (ChromaDB + embeddings)
│   ├── llm.py                 # Llama GGUF wrapper
│   ├── memory.py              # Session conversation memory
│   ├── prompt.py              # LLM prompt builder
│   ├── models.py              # Pydantic schemas
│   ├── requirements.txt
│   ├── .env.example
│   ├── Dockerfile
│   ├── README.md
│   └── data/
│       ├── products.json      # 10 sample products (3 sponsored)
│       └── app_help.json      # 10 app help FAQ items
│
└── glam_pro_chat/             # Flutter chat widget package
    ├── pubspec.yaml
    ├── README.md
    ├── CHANGELOG.md
    ├── lib/
    │   ├── glam_pro_chat.dart
    │   └── src/
    │       ├── models/chat_message.dart
    │       ├── services/api_service.dart
    │       ├── providers/chat_provider.dart
    │       └── widgets/
    │           ├── glam_chat_screen.dart
    │           ├── chat_bubble.dart
    │           ├── chat_input.dart
    │           └── typing_indicator.dart
    └── example/
        ├── pubspec.yaml
        └── lib/main.dart
```

---

## How It Works

```
User types message
       │
       ▼
Flutter GlamProChat widget
  └─ POST /chat  ──────────────────────────────────────┐
                                                        ▼
                                              FastAPI backend
                                                  │
                               ┌──────────────────┼──────────────────┐
                               ▼                  ▼                  ▼
                        ChromaDB             ChromaDB           Session memory
                      (products)            (app_help)         (last 6 exchanges)
                               │                  │                  │
                               └──────────────────┴──────────────────┘
                                                  │
                                                  ▼
                                        Prompt builder
                                                  │
                                                  ▼
                                     Llama 3.2-3B (local GGUF)
                                                  │
                                                  ▼
                                          Reply → Flutter
```

### Key Design Decisions

- **No cloud API calls** – The LLM runs entirely on your hardware.
- **Sponsored boost** – Products with `"sponsored": true` receive a 1.2× retrieval score boost so they surface preferentially when relevant.
- **Separate RAG collections** – Products and app-help use distinct ChromaDB collections to prevent topic bleeding.
- **Session memory** – Limited to the last 6 exchanges to keep prompts within the model's context window.
- **Hot data updates** – Admins POST new JSON files to `/admin/upload/*`; ChromaDB is rebuilt in memory with no server restart.

---

## Integrating into Your Existing Flutter App

```yaml
# pubspec.yaml
dependencies:
  glam_pro_chat:
    git:
      url: https://github.com/your-org/glam_pro_chat.git
      ref: main
```

```dart
import 'package:glam_pro_chat/glam_pro_chat.dart';

// Anywhere in your widget tree:
GlamProChat(
  apiUrl: 'http://api.yourserver.com',
  appBarTitle: 'Beauty Expert',
)
```

---

## License

MIT
