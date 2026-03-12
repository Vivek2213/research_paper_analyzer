# Agentic Research Paper Evaluator

An agent-based FastAPI backend that takes an arXiv paper URL, extracts the paper, analyzes it across multiple review dimensions, and generates a markdown judgement report.

## Why This Project Exists

Research papers are published faster than most people can review them carefully. A paper can look polished while still having weak methodology, unsupported claims, poor novelty, or factual issues. Manual review takes time, and simple LLM summaries are usually not enough because they often:

- collapse important technical details,
- miss inconsistencies between methods and results,
- fail to compare against external literature,
- produce confident but shallow summaries.

This project is built to solve that gap.

Instead of only summarizing a paper, it simulates a lightweight peer-review workflow for arXiv papers by:

- scraping the paper from an arXiv URL,
- parsing the PDF into structured text,
- decomposing the paper into important sections,
- running specialized evaluation agents,
- generating a final judgement report.

## What Problem It Solves

This project helps answer questions such as:

- Does the methodology actually support the claimed results?
- Is the language professional and technically clear?
- Does the work appear novel relative to related literature?
- Which claims should be fact-checked externally?
- Does the paper show signs of overclaiming, weak support, or fabrication risk?

It is useful as a research-assistance tool, assignment project, or prototype auditing layer for technical documents.

## How It Solves The Problem

The pipeline follows this flow:

1. The user submits an arXiv URL.
2. The system normalizes the URL and downloads the PDF.
3. GROBID converts the PDF into TEI XML.
4. The TEI output is parsed into title, full text, and sections.
5. Key sections such as abstract, methodology, results, and conclusion are selected.
6. If enabled, external literature context is retrieved for novelty and fact-check support.
7. Multiple specialized agents evaluate each section:
   - Consistency
   - Grammar & Language
   - Novelty
   - Fact Check
   - Authenticity / Fabrication Risk
8. Section outputs are aggregated.
9. A markdown judgement report is written to the `output/` directory.

## Tech Stack

- Python
- FastAPI
- LangGraph
- LangChain
- Gemini API
- GROBID
- UV package manager
- Docker

## Project Initialization

### 1. Clone the project

```bash
git clone <your-repo-url>
cd research_paper_analyser
```

### 2. Install dependencies with UV

```bash
uv sync
```

### 3. Create environment variables

Create a `.env` file using `.env.example` as reference.

Example:

```env
APP_NAME=Agentic Research Paper Evaluator
APP_DESCRIPTION=API for evaluating research papers from arXiv with agent-based analysis.
APP_VERSION=0.1.0
TEMPLATE_TITLE=Agentic Research Paper Evaluator
TEMPLATE_HEADER=Research Paper Evaluator
TEMPLATE_DESCRIPTION=Multi-agent research paper analysis and judgement report generation
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash-lite
GROBID_URL=http://localhost:8070
MAX_INPUT_TOKENS=10500
CHUNK_OVERLAP_TOKENS=500
MAX_OUTPUT_TOKENS=1200
OUTPUT_DIR=output
EXTERNAL_RETRIEVAL_ENABLED=true
EXTERNAL_SEARCH_MAX_RESULTS=5
```

### 4. Activate the virtual environment

On macOS/Linux:

```bash
source ./.venv/bin/activate
```

On Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 5. Start GROBID

This project requires GROBID as an external dependency for PDF-to-structured-text extraction.

Before running the project:

- open Docker Desktop,
- pull the GROBID image,
- run the container on port `8070`.

You can do that in one command:

```bash
docker run --rm -p 8070:8070 grobid/grobid:0.8.2
```

Once the container is running, the app expects:

```env
GROBID_URL=http://localhost:8070
```

### 6. Run the project

```bash
uv run fastapi dev research_paper_analyser/main.py
```

After startup:

- Home page: `http://127.0.0.1:8000/`
- Swagger docs: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## API Input And Output

### Input

The project currently exposes one main analysis endpoint:

`POST /analyze`

Request body:

```json
{
  "arxiv_url": "https://arxiv.org/abs/2603.08785"
}
```

The request accepts a valid arXiv URL.

### Immediate API Response

The analysis runs in the background. The API immediately returns:

```json
{
  "message": "Analysis started in background.",
  "job_id": "2603.08785-20260312083241",
  "output_path": "output\\2603.08785.md"
}
```

### Final Output

The final output is a markdown report generated in the `output/` directory.

The report includes:

- Executive summary
- Consistency score
- Grammar rating
- Novelty assessment
- Fact-check log
- Accuracy / fabrication risk
- Section-wise notes

## Example Input And Output

An example paper used in this project is:

`https://arxiv.org/pdf/2603.08785`

The generated example output is available at:

[`output/2603.08785_example.md`](/abs/path/c:/code/research_paper_analyser/output/2603.08785.md)

This file shows the style and structure of the judgement report produced by the system.

## Project Structure

The repository is organized as follows:

```text
research_paper_analyser/
|-- research_paper_analyser/
|   |-- api/
|   |   |-- routers/
|   |   |   `-- analyze/
|   |   |       `-- analyze.py
|   |   |-- __init__.py
|   |   `-- ping.py
|   |-- agents/
|   |   |-- __init__.py
|   |   `-- graph.py
|   |-- config/
|   |   |-- __init__.py
|   |   `-- llm_provider_config.py
|   |-- core/
|   |   |-- arxiv.py
|   |   |-- chunker.py
|   |   |-- fetcher.py
|   |   |-- grobid.py
|   |   |-- llm.py
|   |   |-- retrieval.py
|   |   `-- tei_parser.py
|   |-- schemas/
|   |   |-- __init__.py
|   |   |-- analysis.py
|   |   `-- requests.py
|   |-- services/
|   |   |-- __init__.py
|   |   |-- pipeline.py
|   |   `-- report.py
|   |-- utils/
|   |   |-- __init__.py
|   |   |-- logger.py
|   |   `-- templates.py
|   |-- __init__.py
|   `-- main.py
|-- output/
|-- .env
|-- .env.example
|-- pyproject.toml
|-- uv.lock
|-- structure.md
`-- README.md
```

### Folder Responsibilities

- `api/`
  FastAPI routing layer. Handles HTTP endpoints.

- `agents/`
  Agent graph and multi-agent execution flow.

- `config/`
  Central configuration and environment-driven settings.

- `core/`
  Reusable low-level logic such as arXiv handling, chunking, retrieval, PDF fetching, GROBID integration, LLM setup, and TEI parsing.

- `schemas/`
  Pydantic request and analysis result models.

- `services/`
  Application orchestration and report generation.

- `utils/`
  Shared utilities like logging and HTML templates.

- `output/`
  Generated markdown reports.

## Current Workflow Summary

At runtime, the request flow is:

`API -> pipeline -> arXiv fetch -> GROBID -> TEI parse -> section selection -> agent analysis -> aggregation -> markdown report`

## Notes And Requirements

- A valid Gemini API key is required.
- GROBID must be running locally on port `8070`.
- Docker Desktop must be running before starting the GROBID container.
- The project writes generated reports into the `output/` folder.
- Analysis is started asynchronously through FastAPI background tasks.

## Limitations

- The final report quality depends on the quality of the paper extraction from GROBID.
- External retrieval is lightweight and should be treated as supporting context, not a full scholarly search engine.
- The API starts the job in the background and returns immediately; there is currently no dedicated status-tracking endpoint.

## Quick Start

```bash
uv sync
source ./.venv/bin/activate
docker run --rm -p 8070:8070 grobid/grobid:0.8.2
uv run fastapi dev research_paper_analyser/main.py
```

Then send:

```http
POST /analyze
Content-Type: application/json

{
  "arxiv_url": "Arxiv_URL"
}
```
