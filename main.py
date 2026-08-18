"""Interactive resume builder. Run: python main.py --serve"""

import argparse
import json
import os
import re

from dotenv import load_dotenv

try:
    from flask import Flask, jsonify, render_template, request
    from werkzeug.utils import secure_filename
except ImportError:
    Flask = None

try:
    from google import genai
    from google.genai import types as genai_types
except ImportError:
    genai = genai_types = None

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MIN_RESUME_LENGTH = 80
MAX_UPLOAD_SIZE = 2 * 1024 * 1024
DEFAULT_MODEL = "gemini-3.6-flash"

app = Flask(__name__) if Flask is not None else None
if app is not None:
    app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_SIZE


class ResumeError(Exception):
    """Safe error message for the browser."""


def clean_text(text):
    return "\n".join(re.sub(r"\s+", " ", line.strip()) for line in text.splitlines() if line.strip())


def text(value):
    return value.strip() if isinstance(value, str) else ""


def records(value, fields):
    if not isinstance(value, list):
        return []
    return [{field: text(item.get(field)) for field in fields} for item in value if isinstance(item, dict) and any(text(item.get(field)) for field in fields)]


def normalise(data):
    if not isinstance(data, dict):
        raise ResumeError("The extracted resume data was not valid.")
    contact = data.get("contact") if isinstance(data.get("contact"), dict) else {}
    return {
        "name": text(data.get("name")), "headline": text(data.get("headline")), "summary": text(data.get("summary")),
        "skills": [text(item) for item in data.get("skills", []) if text(item)] if isinstance(data.get("skills"), list) else [],
        "education": records(data.get("education"), ("degree", "institution", "year")),
        "experience": records(data.get("experience"), ("role", "company", "dates", "description")),
        "projects": records(data.get("projects"), ("title", "description", "technologies")),
        "achievements": [text(item) for item in data.get("achievements", []) if text(item)] if isinstance(data.get("achievements"), list) else [],
        "contact": {key: text(contact.get(key)) for key in ("email", "phone", "linkedin", "github", "website")},
    }


def validate_resume(raw):
    cleaned = clean_text(raw)
    if not cleaned:
        raise ResumeError("The uploaded file is empty.")
    if len(cleaned) < MIN_RESUME_LENGTH:
        raise ResumeError(f"Resume is too short. Add at least {MIN_RESUME_LENGTH} characters.")
    return cleaned


def extract_with_gemini(resume):
    if genai is None:
        raise ResumeError("Gemini is not installed.")
    load_dotenv(os.path.join(BASE_DIR, ".env"))
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key:
        raise ResumeError("GEMINI_API_KEY is not configured.")
    schema = '''{"name":"string","headline":"string","summary":"string","skills":["string"],"education":[{"degree":"string","institution":"string","year":"string"}],"experience":[{"role":"string","company":"string","dates":"string","description":"string"}],"projects":[{"title":"string","description":"string","technologies":"string"}],"achievements":["string"],"contact":{"email":"string","phone":"string","linkedin":"string","github":"string","website":"string"}}'''
    prompt = f"Convert this resume to JSON using exactly this schema: {schema}. Use only facts in the resume; never invent details. Return JSON only.\n\nRESUME:\n{resume}"
    try:
        response = genai.Client(api_key=key).models.generate_content(
            model=os.getenv("GEMINI_MODEL", "").strip() or DEFAULT_MODEL,
            contents=prompt,
            config=genai_types.GenerateContentConfig(temperature=0.3, response_mime_type="application/json"),
        )
        return normalise(json.loads((response.text or "").strip()))
    except Exception as exc:
        raise ResumeError(f"Gemini is unavailable: {exc}") from exc


def extract_locally(resume):
    """A basic offline extractor for common uppercase resume headings."""
    heading_map = {
        "PROFESSIONAL SUMMARY": "summary", "SUMMARY": "summary", "SKILLS": "skills", "TECHNICAL SKILLS": "skills",
        "EXPERIENCE": "experience", "WORK EXPERIENCE": "experience", "PROJECTS": "projects", "EDUCATION": "education",
        "ACHIEVEMENTS": "achievements", "CERTIFICATIONS": "achievements",
    }
    sections = {name: [] for name in set(heading_map.values())}
    intro, active = [], None
    for line in resume.splitlines():
        heading = heading_map.get(line.upper().rstrip(":"))
        if heading:
            active = heading
        else:
            (sections[active] if active else intro).append(line)

    data = normalise({})
    contacts = {"email": r"^email\s*:\s*(.+)$", "phone": r"^(?:phone|mobile|tel)\s*:\s*(.+)$", "linkedin": r"^linkedin\s*:\s*(.+)$", "github": r"^github\s*:\s*(.+)$", "website": r"^(?:website|portfolio)\s*:\s*(.+)$"}
    details = []
    for line in intro:
        match = next(((key, re.match(pattern, line, re.I)) for key, pattern in contacts.items() if re.match(pattern, line, re.I)), None)
        if match:
            data["contact"][match[0]] = match[1].group(1).strip()
        else:
            details.append(line)
    if details:
        data["name"] = details[0]
    if len(details) > 1:
        data["headline"] = details[1]
    data["summary"] = " ".join(sections["summary"])
    data["skills"] = [item.strip() for line in sections["skills"] for item in re.sub(r"^[^:]+:\s*|^[-*•]\s*", "", line).split(",") if item.strip()]
    data["achievements"] = [re.sub(r"^[-*•]\s*", "", line) for line in sections["achievements"]]

    for index in range(0, len(sections["education"]), 3):
        group = sections["education"][index:index + 3]
        data["education"].append({"degree": group[0], "institution": group[1] if len(group) > 1 else "", "year": group[2] if len(group) > 2 else ""})
    exp = sections["experience"]
    if exp:
        data["experience"].append({"role": exp[0], "company": exp[1] if len(exp) > 1 else "", "dates": "", "description": " ".join(re.sub(r"^[-*•]\s*", "", line) for line in exp[2:])})
    projects = sections["projects"]
    if projects:
        technology = next((line.split(":", 1)[1].strip() for line in projects[1:] if line.lower().startswith("technologies:")), "")
        description = " ".join(line for line in projects[1:] if not line.lower().startswith("technologies:"))
        data["projects"].append({"title": projects[0], "technologies": technology, "description": description})
    return data


def resume_builder():
    return render_template("builder.html")


def extract_uploaded_resume():
    uploaded = request.files.get("resume")
    if uploaded is None or not uploaded.filename:
        return jsonify(error="Please choose a .txt resume file."), 400
    if not secure_filename(uploaded.filename).lower().endswith(".txt"):
        return jsonify(error="Only plain-text (.txt) files are supported."), 400
    try:
        resume = validate_resume(uploaded.read().decode("utf-8"))
    except UnicodeDecodeError:
        return jsonify(error="The file must be UTF-8 encoded plain text."), 400
    except ResumeError as exc:
        return jsonify(error=str(exc)), 400
    try:
        return jsonify(data=extract_with_gemini(resume), source="gemini")
    except ResumeError:
        return jsonify(data=extract_locally(resume), source="local", warning="Gemini could not be reached, so a local text parser was used. Please review the extracted details.")


def upload_too_large(_error):
    return jsonify(error="The file is too large. Please upload a file under 2 MB."), 413


if app is not None:
    app.add_url_rule("/", view_func=resume_builder, methods=["GET"])
    app.add_url_rule("/api/extract", view_func=extract_uploaded_resume, methods=["POST"])
    app.register_error_handler(413, upload_too_large)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Start the interactive resume builder.")
    parser.add_argument("--serve", action="store_true", help="Start the builder at http://127.0.0.1:5000.")
    parser.parse_args(argv)
    if app is None:
        print("[error] Flask is not installed. Run: pip install -r requirements.txt")
        return 1
    app.run(debug=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
