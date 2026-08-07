"""Tests for the AI-Assisted Resume Portfolio Generator.

Covers the mandatory test cases from the project brief:
missing resume file, empty / too-short resume, valid resume,
missing sections, missing API key, API failure, and invalid JSON.
"""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main


# ---------------------------------------------------------------------------
# resume.txt input
# ---------------------------------------------------------------------------


def test_read_missing_file_raises():
    with pytest.raises(main.InputError):
        main.read_and_validate_resume("does-not-exist.txt")


def test_read_empty_file_rejected(tmp_path):
    path = tmp_path / "resume.txt"
    path.write_text("   \n\n  \n", encoding="utf-8")
    with pytest.raises(main.InputError, match="empty"):
        main.read_and_validate_resume(str(path))


def test_read_short_file_rejected(tmp_path):
    path = tmp_path / "resume.txt"
    path.write_text("Hi, my name is Anu.", encoding="utf-8")
    with pytest.raises(main.InputError, match="too short"):
        main.read_and_validate_resume(str(path))


def test_read_valid_resume_returns_cleaned_text(tmp_path):
    path = tmp_path / "resume.txt"
    path.write_text(
        "  John   Doe  \n\n\nDeveloper\n    Python   ,   SQL  \n"
        "Experience: intern at ABC company working on backend APIs\n",
        encoding="utf-8",
    )
    cleaned = main.read_and_validate_resume(str(path))
    assert "  " not in cleaned
    assert "\n\n" not in cleaned
    assert "John" in cleaned


def test_clean_text_removes_extra_spaces_and_blank_lines():
    raw = "   Hello    world\n\n\n   Python   \n\n"
    cleaned = main.clean_text(raw)
    assert cleaned == "Hello world\nPython"


# ---------------------------------------------------------------------------
# JSON handling
# ---------------------------------------------------------------------------


def test_extract_json_plain():
    data = {"name": "Priya", "skills": ["Python"]}
    assert main.extract_json(json.dumps(data)) == data


def test_extract_json_with_markdown_fences():
    raw = "```json\n{\"name\": \"Priya\"}\n```"
    assert main.extract_json(raw) == {"name": "Priya"}


def test_extract_json_with_surrounding_text():
    raw = 'Here is the result: {"name": "Priya"} hope this helps'
    assert main.extract_json(raw) == {"name": "Priya"}


def test_extract_json_invalid_raises():
    with pytest.raises(main.ProjectError, match="Invalid JSON"):
        main.extract_json("this is not json")


def test_extract_json_empty_raises():
    with pytest.raises(main.ProjectError, match="empty"):
        main.extract_json("   ")


def test_validate_and_complete_fills_missing_fields():
    data = main.validate_and_complete({})
    assert data["name"] == ""
    assert data["skills"] == []
    assert data["experience"] == []
    assert data["contact"]["email"] == ""


def test_validate_and_complete_keeps_values_and_drops_garbage():
    data = main.validate_and_complete(
        {
            "name": "  Priya  ",
            "skills": ["Python", "", " SQL ", None],
            "experience": [
                {"role": "Intern", "company": "ABC", "dates": "", "description": ""},
                {"role": "", "company": "", "dates": "", "description": ""},
                "not-a-dict",
            ],
            "contact": {"email": "p@x.com"},
        }
    )
    assert data["name"] == "Priya"
    assert data["skills"] == ["Python", "SQL"]
    assert len(data["experience"]) == 1
    assert data["contact"]["email"] == "p@x.com"


def test_validate_and_complete_rejects_non_object():
    with pytest.raises(main.ProjectError, match="not an object"):
        main.validate_and_complete(["not", "a", "dict"])


# ---------------------------------------------------------------------------
# HTML generation
# ---------------------------------------------------------------------------


def test_build_html_includes_all_sections():
    data = main.validate_and_complete(main.SAMPLE_DATA)
    html = main.build_html(data)
    assert "<title>Priya Sharma</title>" in html
    for section in (
        "id=\"summary\"",
        "id=\"skills\"",
        "id=\"education\"",
        "id=\"experience\"",
        "id=\"projects\"",
        "id=\"achievements\"",
        "id=\"contact\"",
    ):
        assert section in html
    assert "TechNova Solutions" in html
    assert "mailto:priya.sharma@example.com" in html


def test_build_html_hides_empty_sections():
    data = main.validate_and_complete(
        {"name": "Only Name", "skills": [], "contact": {}}
    )
    html = main.build_html(data)
    assert "Only Name" in html
    assert "id=\"skills\"" not in html
    assert "id=\"experience\"" not in html
    assert "id=\"projects\"" not in html
    assert "id=\"contact\"" not in html


def test_build_html_escapes_html():
    data = main.validate_and_complete(
        {"name": "<script>alert('x')</script>", "skills": ["<b>Python</b>"]}
    )
    html = main.build_html(data)
    assert "<script>" not in html
    assert "&lt;script&gt;" in html


# ---------------------------------------------------------------------------
# API key and API failure handling
# ---------------------------------------------------------------------------


def test_get_api_key_missing(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setattr("main.os.getenv", lambda key, default="": "")
    with pytest.raises(main.ConfigError, match="GEMINI_API_KEY"):
        main.get_api_key()


def test_call_gemini_failure_is_wrapped(monkeypatch):
    class BrokenClient:
        class models:
            @staticmethod
            def generate_content(*args, **kwargs):
                raise RuntimeError("network down")

    class FakeGenai:
        @staticmethod
        def Client(**kwargs):
            return BrokenClient()

    monkeypatch.setattr(main, "genai", FakeGenai)
    with pytest.raises(main.GeminiError, match="Gemini API call failed"):
        main.call_gemini("prompt", "fake-key", "gemini-3.6-flash")


def test_call_gemini_empty_response_is_error(monkeypatch):
    class EmptyResponse:
        text = None

    class EmptyClient:
        class models:
            @staticmethod
            def generate_content(*args, **kwargs):
                return EmptyResponse()

    class FakeGenai:
        @staticmethod
        def Client(**kwargs):
            return EmptyClient()

    monkeypatch.setattr(main, "genai", FakeGenai)
    with pytest.raises(main.GeminiError, match="empty"):
        main.call_gemini("prompt", "fake-key", "gemini-3.6-flash")


# ---------------------------------------------------------------------------
# CLI end-to-end (main)
# ---------------------------------------------------------------------------


def test_main_missing_resume_returns_error():
    assert main.main(["--resume", "does-not-exist.txt"]) == 1


def test_main_missing_api_key_returns_error():
    assert main.main(["--resume", main.RESUME_FILE]) == 1


def test_main_demo_generates_output(tmp_path):
    out = tmp_path / "portfolio.html"
    assert main.main(["--demo", "--output", str(out)]) == 0
    assert out.exists()
    assert "Priya Sharma" in out.read_text(encoding="utf-8")
