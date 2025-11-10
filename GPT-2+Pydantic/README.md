## GPT-2 Storyteller (FastAPI + React)

A minimal full‑stack app for generating text with a fine‑tuned GPT‑2 model. This project includes Pydantic validation for ensuring structured and valid input prompt and ensuring the output is structured as well.

### Project structure

```
GPT-2+Pydantic/
  backend/
    app/
      main.py            # FastAPI app and endpoints
      gpt2_handler.py    # GPT‑2 loader/generator
      models.py          # Pydantic schemas + normalization
    requirements.txt
    gpt2-storyteller/    # Place your fine‑tuned model here (ignored by git)
  frontend/
    src/                 # React (Vite) app
    package.json
```

### Requirements

- Python 3.10+
- Node.js 18+

### Backend setup

1. Create and activate a virtual environment (recommended)

```bash
python -m venv .venv
.venv\\Scripts\\activate  # PowerShell on Windows
```

2. Install dependencies

```bash
pip install -r backend/requirements.txt
```

3. Place your fine‑tuned model

- Put your Hugging Face model files (config.json, merges.txt, model.safetensors, tokenizer files, etc.) into `backend/gpt2-storyteller/`.
- The backend auto‑loads from `backend/gpt2-storyteller`. If missing, it falls back to base `gpt2`.

4. Run the API

```bash
python backend/app/main.py
# Server starts at http://localhost:8000
```

### Frontend setup

1. Install dependencies

```bash
cd frontend
npm install
```

2. Run the dev server

```bash
npm run dev
# App at http://localhost:5173
```

### API

- POST `/generate`
  - Body (JSON):
    ```json
    {
      "prompt": "Once upon a time",
      "max_length": 100,
      "temperature": 0.7,
      "top_p": 0.9
    }
    ```
  - Response (JSON):
    ```json
    {
      "generated_text": "Story continues.",
      "prompt": "Once upon a time",
      "model_used": "fine-tuned-gpt-2",
      "processing_time": 0.42
    }
    ```
  - Normalization: ensures the generated text starts with a capital letter and ends with a period.

### Notes on model files (large artifacts)

This repo ignores the fine‑tuned weights directory (`backend/gpt2-storyteller/`) to avoid committing large files.
Place the model locally in that folder before running.

### Publish to GitHub (new repository)

From the project root (`GPT-2+Pydantic/`):

```bash
git init
git add .
git commit -m "Initial commit: GPT-2 storyteller (FastAPI + React)"

# Create a new repo on GitHub first (e.g., https://github.com/<you>/gpt2-storyteller)
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo>.git
git push -u origin main
```

If you already have a repo created with a different default branch, adjust the branch name accordingly.
