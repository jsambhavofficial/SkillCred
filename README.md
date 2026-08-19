# Portfolio Forge

A lightweight web app that turns a plain-text resume into a customisable,
downloadable personal portfolio website.

## Run it

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py --serve
```

Open <http://127.0.0.1:5000> and upload a UTF-8 `.txt` file. The included
`resume.txt` is a ready-to-use example. Review the generated site, choose a
theme, and download a standalone HTML portfolio ready for hosting.

## Features

- Three live portfolio themes: Editorial, Midnight, and Minimal
- Accent colour control
- Standalone HTML export and print support
- Gemini-powered extraction when `GEMINI_API_KEY` is in `.env`
- Offline local extraction fallback when Gemini is unavailable

To enable Gemini, copy `.env.example` to `.env` and add your API key. The app
works without it, using the local fallback parser.
