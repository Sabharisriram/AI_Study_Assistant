# 🤖 AI Study Assistant

An intelligent study assistant that lets you upload PDFs and images, then ask questions about them using RAG (Retrieval-Augmented Generation). Built with FastAPI, Streamlit, Qdrant, and Groq LLM.

---

## 🌐 Live Demo

| Service | URL |
|---|---|
| 🖥️ Frontend (Streamlit) | [aistudyassistant-opuddcrkhctsyg87tnpupu.streamlit.app](https://aistudyassistant-opuddcrkhctsyg87tnpupu.streamlit.app) |
| ⚙️ Backend API (FastAPI) | [sabharisriram-ai-study-assistant-api.hf.space](https://sabharisriram-ai-study-assistant-api.hf.space) |

---

## ✨ Features

- 🔐 User authentication (signup/login) via Supabase
- 📄 PDF upload and intelligent chunking
- 🖼️ Image upload with OCR text extraction
- 🧠 RAG-based Q&A — answers come from your uploaded documents
- 🌐 Web search fallback when document has no relevant content
- 💬 Conversation memory per user
- 👤 Multi-user support — each user's documents are stored separately
- ⚡ Streaming responses

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| Backend | FastAPI + Uvicorn |
| LLM | Groq (LLaMA 3.1 8B) |
| Embeddings | FastEmbed (BAAI/bge-small-en-v1.5) |
| Vector DB | Qdrant Cloud |
| Auth | Supabase |
| OCR | Tesseract |
| Web Search | DuckDuckGo |
| Backend Hosting | HuggingFace Spaces (Docker) |
| Frontend Hosting | Streamlit Cloud |

---

## 🏗️ Architecture

```
User → Streamlit Cloud (Frontend)
            ↓ API calls
    HuggingFace Spaces (FastAPI Backend)
            ↓
    Qdrant Cloud (Vector DB) + Supabase (Auth) + Groq (LLM)
```

---

## 🚀 Run Locally

### 1. Clone the repo
```bash
git clone https://github.com/Sabharisriram/AI_Study_Assistant.git
cd AI_Study_Assistant
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Create `.env` file
```env
GROQ_API_KEY=your_groq_api_key
QDRANT_URL=https://your-cluster.qdrant.tech
QDRANT_API_KEY=your_qdrant_api_key
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key
```

### 4. Run the backend
```bash
uvicorn app.main:app --reload
```

### 5. Run the frontend
```bash
streamlit run streamlit_app.py
```

---

## 📁 Project Structure

```
AI_Study_Assistant/
├── app/
│   ├── main.py
│   ├── routes/
│   │   ├── auth.py
│   │   ├── chat.py
│   │   ├── pdf.py
│   │   └── upload.py
│   └── services/
│       ├── agent_service.py
│       ├── auth_service.py
│       ├── image_service.py
│       ├── memory_service.py
│       ├── rag_service.py
│       └── web_search_service.py
├── streamlit_app.py
├── Dockerfile
├── requirements.txt
└── .env (not committed)
```

---

## 🔑 API Keys Required

- [Groq](https://console.groq.com) — Free LLM API
- [Qdrant Cloud](https://qdrant.tech) — Free vector database
- [Supabase](https://supabase.com) — Free authentication

---

## 👤 Author

**Sabhari Sriram**
- GitHub: [@Sabharisriram](https://github.com/Sabharisriram)