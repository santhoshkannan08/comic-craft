# ComicCraft — AI Comic Story Creator

ComicCraft is a Python FastAPI application that turns a short story idea into a complete 5-panel comic using AI text generation, illustration generation, and PDF export.

## Features

- Story idea form with prompt, character, setting, tone, and art style
- AI-powered 5-panel outline generation using Gemini Flash
- Story expansion with narration, dialogue, and captions using Gemini Pro
- Comic image generation using Stable Diffusion / Diffusers
- Layout assembly for a comic preview
- PDF export through FPDF
- Mock mode for local development without external API costs
- Responsive comic-themed frontend

## Architecture

The project uses a modular FastAPI structure:

- `app/main.py` – app entry point and static assets setup
- `app/routes.py` – HTTP routes and form handling
- `app/models.py` – Pydantic request and content models
- `app/gemini_flash.py` – structured 5-panel outline generation
- `app/gemini_pro.py` – narration and dialogue generation
- `app/image_generator.py` – image generation
- `app/layout_builder.py` – final comic layout assembly
- `app/exporters.py` – PDF generation

## Project Structure

```text
ComicCraft/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── routes.py
│   ├── models.py
│   ├── gemini_flash.py
│   ├── gemini_pro.py
│   ├── image_generator.py
│   ├── layout_builder.py
│   └── exporters.py
├── templates/
│   ├── index.html
│   ├── comic_preview.html
│   └── export_success.html
├── static/
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── script.js
│   ├── panels/
│   └── exports/
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
├── run.py
└── tests/
    └── test_app.py
```

## Prerequisites

- Python 3.11+
- Virtual environment support
- Internet access for Gemini and Hugging Face APIs when using real mode

## Python Installation

### Windows

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
```

### Linux / macOS

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

## Dependency Installation

```bash
pip install -r requirements.txt
```

## Gemini API Key Setup

Create a `.env` file using the example file as a template:

```bash
cp .env.example .env
```

Then edit `.env` and set your keys:

```env
GEMINI_API_KEY=your_gemini_api_key_here
HF_API_KEY=your_huggingface_api_key_here
HF_MODEL_ID=runwayml/stable-diffusion-v1-5
MOCK_MODE=false
```

Never commit `.env` to source control.

## Hugging Face Setup

- Create a free account at Hugging Face.
- Generate an access token from your account settings.
- Add the token to `HF_API_KEY` in `.env`.

For local testing without API costs, set:

```env
MOCK_MODE=true
```

## Running the Application

### Start the server

```bash
uvicorn app.main:app --reload
```

Then open:

- Home page: http://127.0.0.1:8000
- Swagger docs: http://127.0.0.1:8000/docs

## API Endpoints

- `GET /` – Homepage
- `POST /generate` – Form submission to generate a comic
- `POST /generate-comic/json` – JSON-based generation
- `GET /export-success` – PDF export confirmation page
- `GET /test-image` – Generate a sample image
- `GET /health` – Simple health check

## How the AI Pipeline Works

1. Validate form or JSON input.
2. Generate a 5-panel outline with Gemini Flash.
3. Expand each panel into narration, dialogue, and caption using Gemini Pro.
4. Generate one image per panel using Stable Diffusion.
5. Assemble the final comic layout.
6. Render a preview page.
7. Export the result as a PDF.

## Troubleshooting

- Missing environment variables: confirm `.env` exists and contains valid values.
- Gemini errors: verify `GEMINI_API_KEY` and API access.
- Diffusers errors: verify `HF_API_KEY` and compatible PyTorch dependencies.
- PDF export issues: ensure the `static/exports` directory can be created.
- Slow image generation: use `MOCK_MODE=true` for faster local iteration.

## Future Enhancements

- Add user accounts and saved comics
- Enable a queue-based generation job system
- Support additional art models and styles
- Add comic editing before export
- Provide more layout templates and page sizes

## Notes

This project is intentionally simple and modular so it can be used as a foundation for a larger AI comic creation workflow.
