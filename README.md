# Resume Studio

A lightweight web app that turns a plain-text resume into a customisable,
downloadable resume.

## Run it

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py --serve
```

Open <http://127.0.0.1:5000> and upload a UTF-8 `.txt` file. The included
`resume.txt` is a ready-to-use example.

## Features

- Three live templates: Classic, Modern, and Minimal
- Accent, text, and paper colour controls
- HTML, Word-compatible `.doc`, and print-to-PDF downloads
- Gemini-powered extraction when `GEMINI_API_KEY` is in `.env`
- Offline local extraction fallback when Gemini is unavailable

To enable Gemini, copy `.env.example` to `.env` and add your API key. The app
works without it, using the local fallback parser.
