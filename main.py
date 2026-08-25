"""
AI-Assisted Resume Portfolio Generator
=====================================

Reads a plain-text resume (resume.txt), sends it to the Gemini API with a
controlled prompt, receives structured JSON, and generates a portfolio.html
webpage using template.html and style.css.

Usage:
    python main.py              # uses resume.txt and generates portfolio.html
    python main.py --demo       # generate from bundled sample data (no API key needed)
    python main.py --resume FILE
    python main.py --output FILE
"""

import argparse
import html
import json
import os
import re
import sys

from dotenv import load_dotenv

try:
    from google import genai
    from google.genai import types as genai_types
except ImportError:
    genai = None
    genai_types = None

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESUME_FILE = os.path.join(BASE_DIR, "resume.txt")
TEMPLATE_FILE = os.path.join(BASE_DIR, "template.html")
OUTPUT_FILE = os.path.join(BASE_DIR, "portfolio.html")

DEFAULT_MODEL = "gemini-3.6-flash"
MIN_RESUME_LENGTH = 80

# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class ProjectError(Exception):
    """Base error shown to the user in a clean way."""


class ConfigError(ProjectError):
    """Missing or invalid configuration (e.g. API key)."""


class InputError(ProjectError):
    """Invalid resume input file."""


class GeminiError(ProjectError):
    """Problem while calling the Gemini API."""


# ---------------------------------------------------------------------------
# Sample data used only by --demo (for testing without an API key)
# ---------------------------------------------------------------------------

SAMPLE_DATA = {
    "name": "Priya Sharma",
    "headline": "Full-Stack Developer",
    "summary": (
        "Final-year B.Tech Computer Science student with hands-on experience "
        "building web applications with Python, JavaScript, and modern "
        "frontend frameworks."
    ),
    "skills": [
        "Python",
        "JavaScript",
        "Java",
        "SQL",
        "HTML",
        "CSS",
        "React",
        "Django",
        "Flask",
        "MySQL",
        "PostgreSQL",
        "Git",
        "GitHub",
        "REST APIs",
        "JSON",
        "Unit Testing",
    ],
    "education": [
        {
            "degree": "B.Tech in Computer Science and Engineering (AI & ML)",
            "institution": "GLA University, Mathura",
            "year": "2022 - 2026",
        },
        {
            "degree": "Class XII (CBSE), Science with Computer Science",
            "institution": "Delhi Public School, Mathura",
            "year": "2020 - 2022",
        },
    ],
    "experience": [
        {
            "role": "Software Developer Intern",
            "company": "TechNova Solutions",
            "dates": "June 2025 - August 2025",
            "description": (
                "Built REST API endpoints in Django and reduced average "
                "response time by 25%. Automated weekly report generation "
                "with Python scripts and wrote unit tests with pytest."
            ),
        }
    ],
    "projects": [
        {
            "title": "EduTrack - Student Result Management System",
            "description": (
                "A web app to manage student results, generate report cards, "
                "and email them to parents."
            ),
            "technologies": "Python, Django, SQLite, HTML, CSS, Bootstrap",
        },
        {
            "title": "WeatherWise - Weather Dashboard",
            "description": (
                "A weather dashboard that fetches live weather data from a "
                "public API and shows 5-day forecasts with charts."
            ),
            "technologies": "Python, Flask, JavaScript, OpenWeatherMap API",
        },
        {
            "title": "CampusConnect - College Event Platform",
            "description": (
                "A platform where students can discover, register for, and "
                "get reminders about college events."
            ),
            "technologies": "React, Node.js, MongoDB",
        },
    ],
    "achievements": [
        "Secured 1st position in the Smart India Hackathon (College level, 2024).",
        'Completed "Python for Everybody" certification from Coursera (2023).',
        'NPTEL Certification in "Programming, Data Structures and Algorithms" (2024).',
        "Coordinator of the college Coding Club.",
    ],
    "contact": {
        "email": "priya.sharma@example.com",
        "phone": "+91-98765-43210",
        "linkedin": "linkedin.com/in/priyasharma",
        "github": "github.com/priyasharma",
        "website": "",
    },
}

# ---------------------------------------------------------------------------
# Resume input
# ---------------------------------------------------------------------------


def clean_text(text):
    """Remove extra spaces and blank lines from the raw resume text."""
    lines = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line:
            lines.append(re.sub(r"\s+", " ", line))
    return "\n".join(lines)


def read_and_validate_resume(path):
    """Read resume.txt, clean it, and validate it. Returns cleaned text."""
    if not os.path.exists(path):
        raise InputError(f"Resume file not found: {path}")

    try:
        with open(path, "r", encoding="utf-8") as resume_file:
            raw = resume_file.read()
    except (OSError, UnicodeDecodeError) as exc:
        raise InputError(f"Could not read resume file: {exc}") from exc

    cleaned = clean_text(raw)

    if not cleaned:
        raise InputError("Resume file is empty or contains only blank lines.")

    if len(cleaned) < MIN_RESUME_LENGTH:
        raise InputError(
            f"Resume is too short ({len(cleaned)} characters). "
            f"Add at least {MIN_RESUME_LENGTH} characters of meaningful content."
        )

    return cleaned


# ---------------------------------------------------------------------------
# Gemini integration
# ---------------------------------------------------------------------------


def load_env():
    """Load the .env file (if present) into environment variables."""
    load_dotenv(os.path.join(BASE_DIR, ".env"))


def get_api_key():
    """Return the Gemini API key or raise a ConfigError."""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise ConfigError(
            "GEMINI_API_KEY is missing. Copy .env.example to .env, add your key "
            "from Google AI Studio (https://aistudio.google.com/app/apikey), "
            "then run the program again."
        )
    return api_key


def build_prompt(resume_text):
    """Build the prompt that controls what Gemini should generate."""
    return f"""
You are a professional resume analyst. Your task is to convert the resume text
below into structured portfolio content.

RULES:
1. Use ONLY information that is present in the resume. Never invent skills,
   experience, projects, achievements, companies, dates, or links.
2. If any information is missing, use an empty string "" for text fields and
   an empty array [] for list fields. Do NOT make anything up.
3. Keep the professional summary concise (2-3 sentences) and strictly factual.
4. Return ONLY valid JSON. No markdown, no code fences, no extra explanation.

REQUIRED JSON SCHEMA (follow it exactly):
{{
  "name": "string",
  "headline": "string",
  "summary": "string",
  "skills": ["string"],
  "education": [
    {{"degree": "string", "institution": "string", "year": "string"}}
  ],
  "experience": [
    {{"role": "string", "company": "string", "dates": "string", "description": "string"}}
  ],
  "projects": [
    {{"title": "string", "description": "string", "technologies": "string"}}
  ],
  "achievements": ["string"],
  "contact": {{
    "email": "string",
    "phone": "string",
    "linkedin": "string",
    "github": "string",
    "website": "string"
  }}
}}

RESUME TEXT:
\"\"\"
{resume_text}
\"\"\"
""".strip()


def call_gemini(prompt, api_key, model_name):
    """Call the Gemini API and return the raw response text."""
    if genai is None:
        raise ConfigError(
            "The 'google-genai' package is not installed. "
            "Run: pip install -r requirements.txt"
        )

    client = genai.Client(api_key=api_key)

    generation_config = genai_types.GenerateContentConfig(
        temperature=0.4,
        response_mime_type="application/json",
    )

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=generation_config,
        )
    except Exception as exc:
        raise GeminiError(f"Gemini API call failed: {exc}") from exc

    text = (response.text or "").strip() if response else ""
    if not text:
        raise GeminiError("Gemini returned an empty response.")

    return text


# ---------------------------------------------------------------------------
# JSON handling
# ---------------------------------------------------------------------------


def extract_json(raw):
    """Parse the Gemini response into a dict. Tolerates markdown fences."""
    if not raw or not raw.strip():
        raise ProjectError("Gemini returned an empty response.")

    text = raw.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    fenced = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    fenced = re.sub(r"\s*```$", "", fenced).strip()
    try:
        return json.loads(fenced)
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            pass

    raise ProjectError(
        "Invalid JSON received from Gemini. Please check the API key, the model, "
        "and the prompt, then try again."
    )


def as_string(value):
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def as_string_list(value):
    if not isinstance(value, list):
        return []
    return [as_string(item) for item in value if as_string(item)]


def as_record_list(value, keys):
    if not isinstance(value, list):
        return []
    records = []
    for item in value:
        if not isinstance(item, dict):
            continue
        record = {key: as_string(item.get(key)) for key in keys}
        if any(record.values()):
            records.append(record)
    return records


def validate_and_complete(data):
    """Normalise the Gemini JSON and fill missing fields with empty values."""
    if not isinstance(data, dict):
        raise ProjectError("Gemini JSON is not an object.")

    result = {
        "name": as_string(data.get("name")),
        "headline": as_string(data.get("headline")),
        "summary": as_string(data.get("summary")),
        "skills": as_string_list(data.get("skills")),
        "education": as_record_list(
            data.get("education"), ["degree", "institution", "year"]
        ),
        "experience": as_record_list(
            data.get("experience"), ["role", "company", "dates", "description"]
        ),
        "projects": as_record_list(
            data.get("projects"), ["title", "description", "technologies"]
        ),
        "achievements": as_string_list(data.get("achievements")),
        "contact": {
            "email": "",
            "phone": "",
            "linkedin": "",
            "github": "",
            "website": "",
        },
    }

    contact = data.get("contact")
    if isinstance(contact, dict):
        for key in result["contact"]:
            result["contact"][key] = as_string(contact.get(key))

    return result


# ---------------------------------------------------------------------------
# HTML generation
# ---------------------------------------------------------------------------


def escape(text):
    """HTML-escape text safely."""
    return html.escape(as_string(text))


def normalize_url(value):
    value = as_string(value)
    if not value:
        return ""
    if not re.match(r"^https?://", value, re.IGNORECASE):
        return "https://" + value
    return value


def build_summary_section(text):
    if not as_string(text):
        return ""
    return (
        '<section class="section about" id="summary">\n'
        '  <h2><span class="sec-num">01.</span> Professional Summary</h2>\n'
        f'  <p class="summary-text">{escape(text)}</p>\n'
        f"</section>"
    )


def build_skills_section(items):
    if not items:
        return ""
    chips = "".join(f"<li>{escape(item)}</li>" for item in items)
    return (
        '<section class="section" id="skills">\n'
        '  <h2><span class="sec-num">02.</span> Skills</h2>\n'
        f'  <ul class="chip-list">{chips}</ul>\n'
        f"</section>"
    )


def build_achievements_section(items):
    if not items:
        return ""
    rows = "".join(f"<li><span>{escape(item)}</span></li>" for item in items)
    return (
        '<section class="section" id="achievements">\n'
        '  <h2><span class="sec-num">06.</span> Achievements</h2>\n'
        f'  <ol class="achieve-list">{rows}</ol>\n'
        f"</section>"
    )


def build_education_section(records):
    if not records:
        return ""
    items = []
    for record in records:
        title = escape(record.get("degree", ""))
        place = escape(record.get("institution", ""))
        year = escape(record.get("year", ""))
        items.append(
            '<div class="timeline-item">\n'
            f'  <p class="timeline-date">{year}</p>\n'
            f'  <h3>{title}</h3>\n'
            f'  <p class="timeline-place">{place}</p>\n'
            "</div>"
        )
    return (
        '<section class="section" id="education">\n'
        '  <h2><span class="sec-num">05.</span> Education</h2>\n'
        + "\n".join(items)
        + f"\n</section>"
    )


def build_experience_section(records):
    if not records:
        return ""
    items = []
    for record in records:
        role = escape(record.get("role", ""))
        company = escape(record.get("company", ""))
        dates = escape(record.get("dates", ""))
        description = escape(record.get("description", ""))
        meta = " · ".join(part for part in (company, dates) if part)
        desc_html = (
            f'<p class="timeline-desc">{description}</p>' if description else ""
        )
        items.append(
            '<div class="timeline-item">\n'
            f'  <p class="timeline-date">{meta}</p>\n'
            f'  <h3>{role}</h3>\n'
            f"{desc_html}\n"
            "</div>"
        )
    return (
        '<section class="section" id="experience">\n'
        '  <h2><span class="sec-num">03.</span> Experience</h2>\n'
        + "\n".join(items)
        + f"\n</section>"
    )


def build_projects_section(records):
    if not records:
        return ""
    cards = []
    for record in records:
        title = escape(record.get("title", ""))
        description = escape(record.get("description", ""))
        technologies = escape(record.get("technologies", ""))
        tech_html = (
            f'<p class="project-tech">{technologies}</p>' if technologies else ""
        )
        desc_html = (
            f'<p class="project-desc">{description}</p>' if description else ""
        )
        cards.append(
            '<article class="project-card">\n'
            f'  <h3>{title}</h3>\n'
            f"{tech_html}\n"
            f"{desc_html}\n"
            "</article>"
        )
    return (
        '<section class="section" id="projects">\n'
        '  <h2><span class="sec-num">04.</span> Projects</h2>\n'
        '  <div class="project-grid">\n'
        + "\n".join(cards)
        + f"\n  </div>\n</section>"
    )


def build_contact_section(contact):
    items = []

    email = as_string(contact.get("email"))
    if email:
        items.append(
            f'<a class="contact-link" href="mailto:{escape(email)}">{escape(email)}</a>'
        )

    phone = as_string(contact.get("phone"))
    if phone:
        href = re.sub(r"[^0-9+]", "", phone)
        items.append(
            f'<a class="contact-link" href="tel:{escape(href)}">{escape(phone)}</a>'
        )

    for label, key in (
        ("linkedin", "linkedin"),
        ("github", "github"),
        ("website", "website"),
    ):
        value = as_string(contact.get(key))
        if value:
            url = normalize_url(value)
            items.append(
                f'<a class="contact-link" href="{escape(url)}">{escape(label)}</a>'
            )

    if not items:
        return ""

    return (
        '<section class="section contact-section" id="contact">\n'
        '  <h2><span class="sec-num">07.</span> Contact</h2>\n'
        '  <div class="contact-links">\n    '
        + "\n    ".join(items)
        + "\n  </div>\n</section>"
    )


def build_html(data):
    """Insert the portfolio data into template.html and return the full HTML."""
    try:
        with open(TEMPLATE_FILE, "r", encoding="utf-8") as template_file:
            template = template_file.read()
    except (OSError, UnicodeDecodeError) as exc:
        raise ProjectError(f"Could not read the HTML template: {exc}") from exc

    name = as_string(data["name"])
    headline = as_string(data["headline"])

    header_parts = []
    if name:
        header_parts.append(f"<h1>{escape(name)}</h1>")
    if headline:
        header_parts.append(f'<p class="headline">{escape(headline)}</p>')
    if header_parts:
        header = (
            '<header class="header">\n'
            '  <p class="header-tag">// portfolio</p>\n'
            "  " + "\n  ".join(header_parts) + "\n</header>"
        )
    else:
        header = ""

    replacements = {
        "{{HEADER}}": header,
        "{{SUMMARY}}": build_summary_section(data["summary"]),
        "{{SKILLS}}": build_skills_section(data["skills"]),
        "{{EXPERIENCE}}": build_experience_section(data["experience"]),
        "{{PROJECTS}}": build_projects_section(data["projects"]),
        "{{EDUCATION}}": build_education_section(data["education"]),
        "{{ACHIEVEMENTS}}": build_achievements_section(data["achievements"]),
        "{{CONTACT}}": build_contact_section(data["contact"]),
    }

    for placeholder, content in replacements.items():
        template = template.replace(placeholder, content)

    title = name if name else "Portfolio"
    template = template.replace("{{TITLE}}", escape(title))

    # Remove any placeholders that were never filled.
    template = re.sub(r"\{\{[A-Z_]+\}\}", "", template)

    return template


def write_output(path, content):
    """Write the final HTML file."""
    try:
        with open(path, "w", encoding="utf-8") as output_file:
            output_file.write(content)
    except OSError as exc:
        raise ProjectError(f"Could not write the output file: {exc}") from exc


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Convert a resume.txt file into a portfolio.html webpage using Gemini."
    )
    parser.add_argument(
        "--resume", default=RESUME_FILE, help="Path to the resume text file."
    )
    parser.add_argument(
        "--output", default=OUTPUT_FILE, help="Path for the generated portfolio.html."
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Generate the portfolio from bundled sample data (no API key needed).",
    )
    args = parser.parse_args(argv)

    try:
        load_env()

        if args.demo:
            print("[demo] Using bundled sample data (no API call).")
            data = validate_and_complete(SAMPLE_DATA)
        else:
            resume_text = read_and_validate_resume(args.resume)
            print(
                f"[info] Resume loaded and cleaned "
                f"({len(resume_text)} characters)."
            )

            api_key = get_api_key()
            prompt = build_prompt(resume_text)
            model_name = os.getenv("GEMINI_MODEL", "").strip() or DEFAULT_MODEL
            print(f"[info] Calling Gemini model '{model_name}'...")

            raw = call_gemini(prompt, api_key, model_name)
            print("[info] Response received. Parsing JSON...")

            data = validate_and_complete(extract_json(raw))

        html_output = build_html(data)
        write_output(args.output, html_output)

        print(f"[success] Portfolio written to {args.output}")
        print(
            "[tip] Open the file in a browser and verify every detail against "
            "the original resume."
        )

    except ProjectError as exc:
        print(f"[error] {exc}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
