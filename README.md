# Nexa AI — Enterprise Intelligence Platform

A local document-intelligence application for analyzing business documents with a multi-agent workflow. Upload documents, ask for an analysis or comparison, monitor the workflow, and review or export the results.

## Features

- Upload one or more PDF documents and describe the requested analysis in a prompt.
- Extract document text with PDF and Word parsers, with OCR fallback for scanned documents and images.
- Run analysis, comparison, summary, and report workflows.
- Retrieve relevant document context using sentence-transformer embeddings and a local FAISS index.
- Generate executive summaries, structured findings, recommendations, PDF reports, and Excel reports.
- Watch the orchestration agent coordinate ingestion, retrieval, analysis, comparison, and report generation.
- Review, edit, and approve generated report content before downloading updated PDF and Excel files.

## Architecture

- **Frontend:** Single-screen Streamlit document workflow with live agent execution and human report review
- **API:** FastAPI
- **Workflow orchestration:** LangGraph and LangChain
- **Language model:** Ollama; defaults to `qwen2.5:1.5b`
- **Embeddings and vector search:** Sentence Transformers and FAISS
- **Database:** SQLite with SQLAlchemy and `aiosqlite`
- **Reports:** ReportLab (PDF) and OpenPyXL (Excel)

## Requirements

- Python 3.10–3.12
- [Ollama](https://ollama.com/) with a model available locally
- Tesseract OCR for scanned-document and image OCR

The Python dependencies are listed in [`requirements.txt`](./requirements.txt). PyTorch is configured for CPU installation; embedding and language-model tasks may take longer without a GPU.

### Install Tesseract

Install the Tesseract executable using your operating system's package manager. For example:

```bash
# Ubuntu / Debian
sudo apt-get update
sudo apt-get install tesseract-ocr

# macOS with Homebrew
brew install tesseract
```

On Windows, install Tesseract and ensure its executable is on `PATH`.

## Setup

Run these commands from the project root.

### 1. Create and activate a virtual environment

**Linux / macOS**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows PowerShell**

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install Python dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 3. Start Ollama and download the default model

Ensure the Ollama service is running, then:

```bash
ollama pull qwen2.5:1.5b
```

The application also uses the `all-MiniLM-L6-v2` sentence-transformer model. It is downloaded the first time embeddings are created, so the first workflow may take longer and needs access to the model source.

## Run the application

Start the backend and frontend in separate terminals from the project root. Activate the virtual environment in each terminal.

**Terminal 1 — FastAPI**

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 — Streamlit**

```bash
streamlit run frontend/app.py --server.port 8501
```

## Use the application

1. Upload one or more PDFs, choose Analyze, Compare, Summarize, or Generate a report, and describe the task in the prompt.
2. Watch each agent's status and execution log while the orchestration workflow runs. Comparisons require at least two PDFs.
3. Review and edit the generated report, then approve it to regenerate and download PDF and Excel versions.

## API overview

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Check API health |
| `POST` | `/documents/upload` | Upload a document |
| `GET` | `/documents/` | List documents |
| `GET` | `/documents/{doc_id}` | Get a document |
| `DELETE` | `/documents/{doc_id}` | Delete a document |
| `POST` | `/tasks/` | Start an analysis workflow |
| `GET` | `/tasks/` | List workflows |
| `GET` | `/tasks/{task_id}` | Get workflow status and details |
| `GET` | `/analysis/task/{task_id}/result` | Get completed results |
| `GET` | `/analysis/task/{task_id}/download/pdf` | Download a PDF report |
| `GET` | `/analysis/task/{task_id}/download/excel` | Download an Excel report |
| `POST` | `/analysis/calculate` | Evaluate a supported calculator expression |
| `POST` | `/analysis/tco` | Calculate total cost of ownership |
| `POST` | `/analysis/compare-numeric` | Compare numeric values |

## Configuration and stored data

The application reads these optional environment variables:

| Variable | Default | Description |
| --- | --- | --- |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `qwen2.5:1.5b` | Ollama model name |

The database and generated files are stored under `data/`:

- `data/app.db` — SQLite database
- `data/documents/` — uploaded documents
- `data/vector_store/` — FAISS indexes and metadata
- `data/reports/` — generated PDF and Excel reports

These files are local application data; back them up if they need to be retained. Do not commit uploaded documents, database contents, or generated reports.

