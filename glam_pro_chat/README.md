# glam_pro_chat

A self-contained, production-ready Flutter chat widget for the **Glam Pro Beauty Assistant** AI chatbot.

Drop a single widget into any Flutter app to get a fully styled, bilingual (Arabic/English) AI beauty advisor powered by a local LLM backend.

---

## Features

| Feature | Detail |
|---|---|
| 🌹 **Premium Design** | Deep rose & antique gold palette, Poppins typography, gradient app bar |
| 🌐 **Arabic / English** | RTL-aware layout; the AI replies in the user's language |
| 💬 **Multi-turn chat** | Session memory on the backend; seamless conversation flow |
| ⏳ **Typing indicator** | Animated three-dot bounce while the assistant replies |
| ⚠️ **Error states** | Friendly connection-error screen with retry button |
| 🔌 **Configurable URL** | Point to any running backend via a single `apiUrl` parameter |
| 📦 **Zero platform channels** | Pure Dart – works on Android, iOS, Web, and Desktop |

---

## Installation

### Via local path (development)
```yaml
dependencies:
  glam_pro_chat:
    path: ../glam_pro_chat
```

### Via GitHub (production)
```yaml
dependencies:
  glam_pro_chat:
    git:
      url: https://github.com/your-org/glam_pro_chat.git
      ref: main
```

Then run:
```bash
flutter pub get
```

---

## Quick Start

```dart
import 'package:glam_pro_chat/glam_pro_chat.dart';

// Inside a Scaffold or as the full app body:
GlamProChat(
  apiUrl: 'http://192.168.1.10:8000',  // Your backend IP
  appBarTitle: 'Glam Pro Assistant',    // Optional
)
```

That's it. The widget handles session creation, message sending, typing indicators, and error recovery automatically.

---

## API URL Notes

| Platform | URL to use |
|---|---|
| Android emulator | `http://10.0.2.2:8000` |
| iOS simulator | `http://127.0.0.1:8000` |
| Physical device | `http://<your-LAN-IP>:8000` |
| Production | `https://api.yourserver.com` |

---

## Widget Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `apiUrl` | `String` | **required** | Base URL of the Glam Pro backend |
| `appBarTitle` | `String` | `'Glam Pro Assistant'` | Title in the chat app bar |
| `inputHint` | `String` | `'Ask me anything about beauty…'` | Placeholder text in the input field |

---

## Design Tokens

| Token | Value | Usage |
|---|---|---|
| Rose | `#D4467B` | User bubbles, send button, accents |
| Deep rose | `#9B2456` | App bar gradient end |
| Gold | `#C9A84C` | Accent icon, gradient divider |
| Blush white | `#FFF5F8` | Background |
| Dark plum | `#2D1B2E` | Body text |
| Font | Poppins | All text (via google_fonts) |

---

## Package Structure

```
lib/
├── glam_pro_chat.dart          # Public barrel export
└── src/
    ├── models/
    │   └── chat_message.dart   # ChatMessage data class
    ├── services/
    │   └── api_service.dart    # HTTP client (GlamApiService)
    ├── providers/
    │   └── chat_provider.dart  # ChangeNotifier state manager
    └── widgets/
        ├── glam_chat_screen.dart  # GlamProChat (main widget)
        ├── chat_bubble.dart       # Individual message bubble
        ├── chat_input.dart        # Text field + send button
        └── typing_indicator.dart  # Animated three-dot indicator
```

---

## Backend

The widget communicates with the **Glam Pro Python backend** (FastAPI + Llama 3.2-3B + ChromaDB). See the `backend/` directory for full setup instructions.

Endpoints used:
- `GET  /session/new` – creates a conversation session
- `POST /chat` – sends a message, returns the AI reply

---

## Example App

The `example/` directory contains a minimal Flutter app that demonstrates integration:

```bash
cd example
flutter pub get
flutter run
```

> Make sure your backend is running before launching the example.

---

## Requirements

- Flutter `>=3.19.0`
- Dart `>=3.3.0`
- Dependencies: `http`, `provider`, `intl`, `google_fonts`
