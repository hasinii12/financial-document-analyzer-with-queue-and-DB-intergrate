# Financial Document Analyzer

An AI-powered financial document analysis system built with CrewAI, FastAPI, SQLite, and Celery. This system processes corporate reports, financial statements, and investment documents using intelligent AI agents.

---

## Bugs Found and Fixed

### 1. `agents.py` — Undefined LLM Variable
**Bug:** `llm = llm` — self-referencing undefined variable causing a `NameError` on startup.

**Fix:** Replaced with a proper LLM initialization:
```python
from crewai import Agent, LLM
llm = LLM(model="groq/llama-3.3-70b-versatile", api_key=os.environ.get("GROQ_API_KEY"))
```

---

### 2. `agents.py` — Wrong Parameter Name for Tools
**Bug:** `tool=[...]` — incorrect parameter name, CrewAI expects `tools`.

**Fix:**
```python
# Before
tool=[FinancialDocumentTool.read_data_tool]

# After
tools=[FinancialDocumentTool.read_data_tool]
```

---

### 3. `agents.py` — Irresponsible Agent Goals and Backstories
**Bug:** All agent `goal` and `backstory` fields instructed agents to fabricate data, ignore compliance, make up URLs, contradict themselves, and give harmful financial advice.

**Fix:** Replaced all agent definitions with professional, accurate, compliance-aware descriptions that base analysis strictly on document data and include appropriate disclaimers.

---

### 4. `tools.py` — Missing Import for PDF Loader
**Bug:** `Pdf` class was used but never imported, causing a `NameError`.

**Fix:**
```python
# Before
docs = Pdf(file_path=path).load()

# After
from langchain_community.document_loaders import PyPDFLoader
docs = PyPDFLoader(file_path=path).load()
```

---

### 5. `tools.py` — Async Methods Not Supported by CrewAI
**Bug:** Tool methods were defined as `async def`, but CrewAI requires synchronous tool functions.

**Fix:** Removed `async` keyword from all tool methods.

---

### 6. `tools.py` — Plain Functions Instead of BaseTool Instances
**Bug:** CrewAI requires tools to be proper `BaseTool` instances, but methods were plain Python functions causing a `ValidationError`.

**Fix:** Added `@tool` decorator with type annotations:
```python
from crewai.tools import tool

class FinancialDocumentTool():
    @tool("Read Financial Document")
    def read_data_tool(path: str = 'data/sample.pdf') -> str:
        ...
```

---

### 7. `main.py` — Route Handler Shadowing Imported Task
**Bug:** The FastAPI route handler `async def analyze_financial_document(...)` had the same name as the imported `analyze_financial_document` task from `task.py`, causing a `TypeError` at runtime.

**Fix:** Renamed the import and route handler:
```python
# Import renamed
from task import analyze_financial_document as analyze_financial_document_task

# Route handler renamed
async def analyze_document(...):
```

---

### 8. `main.py` — reload=True Causing Constant Crashes
**Bug:** `uvicorn.run(app, reload=True)` caused WatchFiles to monitor the entire venv directory, triggering constant `KeyboardInterrupt` crashes.

**Fix:**
```python
uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
```

---

### 9. `task.py` — Hallucination-Encouraging Task Descriptions
**Bug:** All task `description` and `expected_output` fields instructed the agent to fabricate URLs, contradict itself, ignore the user's query, and make up financial data.

**Fix:** Replaced with structured, accurate, evidence-based task definitions that require agents to cite specific data from the document.

---

## Tech Stack

- **FastAPI** — REST API framework
- **CrewAI** — AI agent orchestration
- **Groq API** — LLM provider (llama-3.3-70b-versatile)
- **SQLite + SQLAlchemy** — Database for storing results
- **Celery + Redis** — Queue worker for concurrent requests
- **LangChain + PyPDF** — PDF document processing
- **SerperDev** — Web search tool for agents

---

## Setup Instructions

### Prerequisites
- Python 3.11+
- Redis installed on your system

### Step 1 — Clone the Repository
```bash
git clone https://github.com/yourusername/financial-document-analyzer.git
cd financial-document-analyzer
```

### Step 2 — Create Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
```

### Step 3 — Install Dependencies
```bash
pip install crewai==0.130.0 crewai-tools==0.47.1 fastapi uvicorn python-dotenv langchain-community pypdf groq celery redis sqlalchemy python-multipart
```

### Step 4 — Configure Environment Variables
Create a `.env` file in the project root:
```env
GROQ_API_KEY=your_groq_api_key_here
SERPER_API_KEY=your_serper_api_key_here
```

Get your free API keys:
- Groq API: https://console.groq.com/keys
- Serper API: https://serper.dev

### Step 5 — Run the Project

**Terminal 1 — Start Redis:**
```bash
& "C:\Program Files\Redis\redis-server.exe" "C:\Program Files\Redis\redis.windows.conf"
```

**Terminal 2 — Start Celery Worker:**
```bash
cd financial-document-analyzer
venv\Scripts\activate
celery -A celery_worker worker --loglevel=info --concurrency=4
```

**Terminal 3 — Start FastAPI Server:**
```bash
cd financial-document-analyzer
venv\Scripts\activate
python main.py
```

### Step 6 — Access the API
Open your browser at:
```
http://localhost:8000/docs
```

---

## API Documentation

### Base URL
```
http://localhost:8000
```

---

### GET `/`
Health check endpoint.

**Response:**
```json
{
  "message": "Financial Document Analyzer API is running"
}
```

---

### POST `/analyze`
Analyze a financial document synchronously. Result is saved to the database.

**Request:**
- `file` (required): PDF file upload
- `query` (optional): Analysis query string (default: "Analyze this financial document for investment insights")

**Example:**
```bash
curl -X POST "http://localhost:8000/analyze" \
  -F "file=@document.pdf" \
  -F "query=What are the key revenue trends?"
```

**Response:**
```json
{
  "status": "success",
  "job_id": "uuid-string",
  "query": "What are the key revenue trends?",
  "analysis": "Detailed analysis here...",
  "file_processed": "document.pdf"
}
```

---

### POST `/analyze/async`
Submit a document for asynchronous analysis via Celery queue. Handles concurrent requests without blocking.

**Request:**
- `file` (required): PDF file upload
- `query` (optional): Analysis query string

**Response:**
```json
{
  "status": "queued",
  "job_id": "uuid-string",
  "message": "Document submitted for analysis. Use /analyze/status/{job_id} to check progress."
}
```

---

### GET `/analyze/status/{job_id}`
Check the status of an async analysis job.

**Response:**
```json
{
  "job_id": "uuid-string",
  "status": "completed",
  "filename": "document.pdf",
  "query": "What are the key revenue trends?",
  "result": "Detailed analysis here...",
  "created_at": "2026-02-26T10:00:00",
  "completed_at": "2026-02-26T10:01:30"
}
```

Status values: `pending` → `processing` → `completed` / `failed`

---

### GET `/analyses`
Retrieve all past analysis results from the database.

**Response:**
```json
{
  "total": 5,
  "analyses": [
    {
      "job_id": "uuid-string",
      "filename": "document.pdf",
      "query": "Analyze revenue trends",
      "status": "completed",
      "created_at": "2026-02-26T10:00:00",
      "completed_at": "2026-02-26T10:01:30"
    }
  ]
}
```

---

### GET `/analyses/{job_id}`
Retrieve a specific analysis result by job ID.

---

### DELETE `/analyses/{job_id}`
Delete a specific analysis result from the database.

---

### POST `/users`
Create a new user.

**Parameters:**
- `name`: User's name
- `email`: User's email (must be unique)

**Response:**
```json
{
  "user_id": "uuid-string",
  "name": "John Doe",
  "email": "john@example.com",
  "created_at": "2026-02-26T10:00:00"
}
```

---

### GET `/users`
Retrieve all users from the database.

---

## Project Structure

```
financial-document-analyzer/
├── main.py              # FastAPI app with all endpoints
├── agents.py            # CrewAI agent definitions
├── task.py              # CrewAI task definitions
├── tools.py             # Custom PDF and analysis tools
├── database.py          # SQLite database models and setup
├── celery_worker.py     # Celery queue worker
├── .env                 # API keys (not committed to git)
├── .env.example         # Example environment variables
├── .gitignore           # Git ignore rules
├── requirements.txt     # Python dependencies
├── data/                # Uploaded PDFs (temporary)
└── outputs/             # Analysis outputs
```

---

## Bonus Features Implemented

### Queue Worker Model (Redis + Celery)
- Concurrent request handling with 4 parallel workers
- Async endpoint (`POST /analyze/async`) that returns immediately with a `job_id`
- Job status tracking (`GET /analyze/status/{job_id}`)
- Automatic retry on failure (up to 3 retries with exponential backoff)

### Database Integration (SQLite)
- Stores all analysis results with status tracking
- User management system
- Full CRUD operations for analysis history
- Automatic database initialization on startup

