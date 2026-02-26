# 🧠 Second-Brain-AI

SecondBrain is a full-stack AI application that allows users to **ingest knowledge from multiple sources** and **query that knowledge using Retrieval-Augmented Generation (RAG)**.

All responses are grounded strictly in ingested content using semantic search and citations.

---

## ✨ Features

### 🔹 Multi-Source Ingestion
Ingest knowledge from:
- **Plain text**
- **Documents** (PDF, DOCX, TXT)
- **Web URLs** (HTML extraction)
- **Audio files** (`.wav`, `.mp3`) via OpenAI Whisper transcription

Each source flows through a unified ingestion pipeline.

---

### 🔹 Retrieval-Augmented Chat (RAG)
- Queries are embedded and matched against stored document chunks
- Relevant chunks retrieved using vector similarity
- Responses generated **only from retrieved context**
- Citations returned with every response

This prevents hallucinations and ensures traceability.

---

### 🔹 Streaming Responses
- Token-by-token streaming via Server-Sent Events (SSE)
- Metadata (conversation ID + citations) sent before stream starts
- Real-time chat experience in the frontend

---

### 🔹 Persistent Conversations
- Conversations stored in PostgreSQL
- Multi-turn chat supported
- Citations stored per assistant message

---

## 🏗️ Architecture

### Backend
- **FastAPI** (async)
- **PostgreSQL + pgvector**
- **SQLAlchemy (async)**
- **OpenAI APIs**
  - Embeddings (`text-embedding-3-small`)
  - Whisper (`whisper-1`)
  - Chat completions (streaming)

### Frontend
- **Next.js (App Router)**
- **React + TypeScript**
- **Tailwind CSS**
- **SSE streaming client**

---

## 🔄 Ingestion Pipeline

Each document passes through:

1. **Extract** – parse text, scrape web, or transcribe audio  
2. **Chunk** – split text into semantic chunks  
3. **Embed** – generate embeddings for each chunk  
4. **Store** – save chunks + vectors in PostgreSQL  
5. **Ready** – document becomes searchable  

Job status is tracked per document.

---

## ⚠️ Important Design Notes

- Retrieval is **purely similarity-based**
- The system does **not auto-include the most recent document**
- If no relevant chunks are found, the model responds with limited context
- Audio files are transcribed before entering retrieval
- Image ingestion is scaffolded but not fully implemented

These behaviors mirror real-world RAG systems.

---

## 🚀 Getting Started

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/HarshalDevi/Second-Brain-AI.git
cd Second-Brain-AI
🧩 Backend Setup
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
Environment Variables

Create a .env file inside the backend/ directory:

cp .env.example .env

Fill in:

OPENAI_API_KEY=your_openai_api_key_here
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/secondbrain
Run Backend
uvicorn app.main:app --reload --port 8000

Backend will be available at:

http://localhost:8000
🎨 Frontend Setup
cd frontend
npm install
Environment Variable

Create .env.local inside frontend/:

NEXT_PUBLIC_API_BASE=http://localhost:8000
Run Frontend
npm run dev

Frontend will be available at:

http://localhost:3000
🧪 Example Queries

“What did I fix recently?”

“Summarize the audio I uploaded”

“What problems were discussed in the meeting?”

“What are the key points from the document?”

📂 Project Structure
Second-Brain-AI/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── db/
│   │   ├── models/
│   │   └── services/
│   ├── uploads/
│   ├── .env.example
│   ├── Dockerfile
│   ├── requirements.txt
│   └── railway.json
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   └── lib/
│   ├── public/
│   ├── .env.local
│   ├── package.json
│   └── tailwind.config.ts
│
├── docker-compose.yml
└── README.md
🛠️ Tech Stack

FastAPI

PostgreSQL + pgvector

SQLAlchemy (async)

OpenAI APIs

Next.js

React

Tailwind CSS

