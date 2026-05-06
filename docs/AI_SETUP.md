# AI Setup Guide

## Overview

InfraMind AI uses the Python backend in `backend/` for real infrastructure analysis. The backend parses uploaded files, builds structured prompts, calls OpenAI, and returns normalized findings for the web UI.

## Environment variables

Set these values in `backend/.env`:

```env
OPENAI_API_KEY=your-key
OPENAI_MODEL=gpt-4.1
OPENAI_TIMEOUT_SECONDS=45
OPENAI_MAX_RETRIES=2
OPENAI_TEMPERATURE=0.1
USE_MOCK_AI=false
```

Set this in the root `.env` for the web app:

```env
NEXT_PUBLIC_ANALYSIS_API_URL=http://localhost:8000
```

## Local backend start

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Demo tips

- Use the intentionally risky files in `samples/`.
- Upload a mix of Terraform and Kubernetes to show category diversity.
- Keep the OpenAI model set to `gpt-4.1` for the strongest demo quality.
- If the API key is missing, the backend falls back to heuristic analysis so the upload flow still completes.