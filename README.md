# Education RAG

A college-level educational AI system with hierarchical RAG, summarization, and **modern web UI**.

## 🎯 Overview

Complete full-stack application featuring:
- **Modern React UI** - Dark theme, ChatGPT-style interface
- **Hierarchical Content** - Subject → Unit → Topic organization
- **Smart RAG** - Intent classification with context-aware retrieval
- **Document Processing** - PDF, DOCX, TXT, MD support
- **Dual Vector Stores** - Separate indexes for chunks and summaries
- **Multi-user Support** - Isolated data per user (auth stub)

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- OpenAI API key

### 1. Backend Setup

```bash
# Navigate to project root
cd /root/education_rag

# Activate virtual environment
source venv/bin/activate

# Configure OpenAI API (REQUIRED)
# Edit .env and add:
# OPENAI_API_KEY=sk-your-key-here

# Start backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will run at: **http://localhost:8000**

### 2. Frontend Setup

```bash
# In a NEW terminal, navigate to frontend
cd /root/education_rag/frontend

# Install dependencies (first time only)
npm install

# Start development server
npm run dev
```

Frontend will run at: **http://localhost:5173**

### 3. Access the Application

Open your browser to: **http://localhost:5173**

You'll see:
- **Left Sidebar**: Subject/Unit/Topic tree navigation
- **Main Area**: Chat interface (ChatGPT-style)

## 📖 Complete Usage Guide

### Step 1: Create Data Structure (via API)

The UI currently displays existing data. To add content, use the backend API:

```bash
# Create a user
curl -X POST http://localhost:8000/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "email": "alice@example.com"}'

# Create a subject
curl -X POST http://localhost:8000/api/v1/subjects \
  -H "Content-Type: application/json" \
  -H "X-User-Id: 1" \
  -d '{"name": "Data Structures", "description": "Computer Science fundamentals"}'

# Create a unit
curl -X POST http://localhost:8000/api/v1/subjects/1/units \
  -H "Content-Type: application/json" \
  -H "X-User-Id: 1" \
  -d '{"title": "Search Algorithms", "description": "Binary and linear search"}'

# Create a topic
curl -X POST http://localhost:8000/api/v1/subjects/1/units/1/topics \
  -H "Content-Type: application/json" \
  -H "X-User-Id: 1" \
  -d '{"title": "Binary Search"}'
```

### Step 2: Upload Documents

```bash
# Upload a PDF or document
curl -X POST http://localhost:8000/api/v1/subjects/1/units/1/topics/1/files \
  -H "X-User-Id: 1" \
  -F "file=@your-document.pdf"
```

### Step 3: Process Content

```bash
# Chunk the documents
curl -X POST http://localhost:8000/api/v1/subjects/1/units/1/topics/1/chunk \
  -H "X-User-Id: 1"

# Generate embeddings
curl -X POST http://localhost:8000/api/v1/subjects/1/units/1/topics/1/embed \
  -H "X-User-Id: 1"

# Generate topic summary
curl -X POST http://localhost:8000/api/v1/subjects/1/units/1/topics/1/summarize \
  -H "X-User-Id: 1"

# Generate unit summary
curl -X POST http://localhost:8000/api/v1/subjects/1/units/1/summarize \
  -H "X-User-Id: 1"

# Embed summaries
curl -X POST http://localhost:8000/api/v1/subjects/1/units/1/embed-summaries \
  -H "X-User-Id: 1"
```

### Step 4: Use the Web UI

1. **Refresh the frontend** - Click the refresh button in the sidebar
2. **Expand the subject** - Click on "Data Structures"
3. **Expand the unit** - Click on "Search Algorithms"  
4. **Select the topic** - Click on "Binary Search"
5. **Start chatting** - Type questions in the input box!

## 🎨 UI Features

### Dark Mode Design
- Near-black background (#0a0a0b)
- Subtle borders and accents
- Clean, minimal aesthetic
- Professional color scheme

### Chat Interface
- User messages: Right-aligned, blue
- AI messages: Left-aligned, dark gray
- Markdown support (code blocks, inline code)
- Collapsible source references
- Loading indicators

### Navigation
- Expandable tree structure
- Visual hierarchy (icons for subjects/units/topics)
- Active topic highlighting
- Refresh button for reloading data

### Context Awareness
- Chat disabled until topic selected
- Chat history preserved per topic
- Context indicator in header

## 🏗️ Architecture

### Frontend Stack
- **React 19** + **TypeScript**
- **Vite** for fast builds
- **Tailwind CSS** for styling
- **Fetch API** for backend communication

### Backend Stack
- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - ORM with SQLite
- **FAISS** - Vector similarity search
- **OpenAI** - Embeddings (text-embedding-3-small) & LLM (gpt-4o-mini)
- **PyPDF2** - PDF extraction
- **python-docx** - DOCX extraction

### Project Structure

```
/education_rag
├── app/                    # Backend (Python/FastAPI)
│   ├── api/routes/        # API endpoints
│   │   ├── chat.py        # Chat endpoint
│   │   ├── summaries.py   # Summary generation
│   │   ├── subjects.py    # Subject CRUD
│   │   ├── units.py       # Unit CRUD
│   │   ├── topics.py      # Topic CRUD
│   │   ├── files.py       # File upload
│   │   └── rag.py         # RAG debug endpoints
│   ├── models/            # SQLAlchemy models
│   ├── schemas/           # Pydantic schemas
│   ├── services/          # Business logic
│   │   ├── chat_service.py       # Intent + RAG
│   │   ├── summary_service.py    # Summarization
│   │   └── retrieval_service.py  # FAISS retrieval
│   └── utils/             # Utilities
│       ├── llm.py                # OpenAI LLM
│       ├── prompts.py            # Prompt templates
│       ├── vector_store.py       # Chunk FAISS index
│       └── summary_vector_store.py # Summary FAISS index
│
└── frontend/               # Frontend (React/TypeScript)
    ├── src/
    │   ├── components/    # React components
    │   │   ├── Sidebar.tsx
    │   │   ├── SubjectTree.tsx
    │   │   ├── ChatWindow.tsx
    │   │   ├── ChatInput.tsx
    │   │   └── MessageBubble.tsx
    │   ├── api/
    │   │   └── client.ts  # Backend API client
    │   ├── types/
    │   │   └── index.ts   # TypeScript types
    │   ├── App.tsx        # Main app component
    │   └── main.tsx       # Entry point
    └── tailwind.config.js # Tailwind configuration
```

## 🤖 Intent Classification

The chat system automatically classifies user questions:

| Intent | Retrieval Strategy | Example Question |
|--------|-------------------|------------------|
| **teach_from_start** | Unit summaries | "Teach me about sorting algorithms" |
| **explain_topic** | Topic summaries + chunks | "What is binary search?" |
| **explain_detail** | Raw chunks only | "How does the pivot selection work?" |
| **revise** | Unit summaries | "Quick review of search algorithms" |
| **generate_questions** | Topic summaries | "Give me practice questions on binary search" |

## 🔧 Configuration

### Backend (.env)

```bash
# Required
OPENAI_API_KEY=sk-your-key-here

# Optional (defaults shown)
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_LLM_MODEL=gpt-4o-mini
DATABASE_URL=sqlite:///./data/education_rag.db
CHUNK_MIN_TOKENS=300
CHUNK_MAX_TOKENS=600
CHUNK_OVERLAP_PERCENT=15
```

### Frontend

API base URL is configured in `src/api/client.ts`:
```typescript
const API_BASE = 'http://localhost:8000/api/v1';
```

Change this if your backend runs on a different host/port.

## 📡 API Endpoints

### Main Endpoints

- **POST /api/v1/subjects/{id}/chat** - Chat with RAG
- **POST /api/v1/subjects** - Create subject
- **GET /api/v1/subjects** - List subjects
- **POST /api/v1/subjects/{id}/units** - Create unit
- **GET /api/v1/subjects/{id}/units** - List units
- **POST /api/v1/subjects/{s}/units/{u}/topics** - Create topic
- **GET /api/v1/subjects/{s}/units/{u}/topics** - List topics

### Processing Endpoints

- **POST .../topics/{t}/files** - Upload file
- **POST .../topics/{t}/chunk** - Chunk files
- **POST .../topics/{t}/embed** - Embed chunks
- **POST .../topics/{t}/summarize** - Generate topic summary
- **POST .../units/{u}/summarize** - Generate unit summary
- **POST .../units/{u}/embed-summaries** - Embed summaries

### Interactive API Docs

Full API documentation available at: **http://localhost:8000/docs**

## 🐛 Troubleshooting

### "30 Problems" Warning in VS Code

These are Pylance type warnings about `Annotated` types - they're cosmetic and don't affect functionality. The app runs perfectly.

### Frontend Can't Connect to Backend

- Ensure backend is running on port 8000
- Check CORS is enabled (already configured)
- Verify API_BASE in `frontend/src/api/client.ts`

### No Subjects Appearing in UI

- Create subjects via API (see Step 1 above)
- Click refresh button in sidebar
- Check browser console for errors

### Chat Returns "Not found in your uploaded material"

- Upload documents to the topic
- Run chunking and embedding
- Generate summaries
- Ensure topic is selected in UI

### OpenAI API Errors

- Verify OPENAI_API_KEY in `.env`
- Check API key has sufficient credits
- Restart backend after changing `.env`

## 🚀 Development Commands

### Backend

```bash
# Run server with auto-reload
uvicorn app.main:app --reload

# Run on specific host/port
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Check syntax
python -c "import app.main"
```

### Frontend

```bash
# Development mode (hot reload)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

## 📦 Technologies Used

### Backend
- **FastAPI** - Web framework
- **SQLAlchemy** - ORM
- **SQLite** - Database
- **FAISS** - Vector search (CPU)
- **OpenAI** - Embeddings & LLM
- **PyPDF2** - PDF parsing
- **python-docx** - DOCX parsing
- **tiktoken** - Token counting

### Frontend
- **React 19** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **Fetch API** - HTTP client

## 🎓 Example Workflow

1. **Create subject**: "Machine Learning"
2. **Create unit**: "Supervised Learning"
3. **Create topic**: "Linear Regression"
4. **Upload PDFs**: Upload lecture notes, textbooks
5. **Process**: Chunk → Embed → Summarize
6. **Chat**: 
   - "Teach me about linear regression" → Gets unit summary
   - "Explain the cost function" → Gets topic summary + chunks
   - "Show me the gradient descent formula" → Gets detailed chunks
   - "Give me practice problems" → Generates questions from content

## 📄 License

MIT

## 🙋 Support

- Backend API docs: http://localhost:8000/docs
- Frontend dev server: http://localhost:5173
- Issues: Check browser console and backend logs
