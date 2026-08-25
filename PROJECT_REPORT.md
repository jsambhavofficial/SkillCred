# Project Report
## AI-Assisted Resume Portfolio Generator

| | |
| --- | --- |
| **Project type** | Group project |
| **Group size** | 5 students |
| **Duration** | 3 weeks |
| **Course** | AIML GLA Bootcamp '26 |
| **Technologies** | Python, Gemini API, JSON, HTML, CSS, Git/GitHub |
| **Submission** | Mandatory GitHub repository |
| **Hosting** | Optional |

---

## 1. Introduction

The **AI-Assisted Resume Portfolio Generator** is a simple command-line
application that converts plain resume text into a professional portfolio
webpage.

One `resume.txt` file goes into the Python program. The program:

1. Reads and cleans the resume text.
2. Sends it to the **Gemini API** using a carefully controlled prompt.
3. Receives structured **JSON**.
4. Converts the JSON into Python lists and dictionaries.
5. Generates a readable **portfolio.html** webpage using a separate HTML template
   and CSS stylesheet.

The core goal of the project is not to build a complex website, but to learn and
demonstrate: Python file handling, API usage, JSON handling, prompt design, HTML
generation, testing, and responsible use of AI.

---

## 2. Objectives

- Read and clean resume text using Python.
- Send the resume to Gemini using a clear and controlled prompt.
- Receive the output in **valid JSON** format.
- Convert the JSON response into Python lists and dictionaries.
- Generate a readable portfolio webpage using HTML and CSS.
- Verify that every piece of generated content is supported by the resume.
- Submit the complete project through GitHub.

---

## 3. Required Technologies

| Technology | Purpose in this project |
| --- | --- |
| **Python** | Read files, call the Gemini API, process JSON, and generate HTML |
| **Gemini API** | Extract and rewrite resume content into portfolio structure |
| **JSON** | Store the generated portfolio content in a structured format |
| **HTML** | Create the portfolio webpage |
| **CSS** | Style the portfolio |
| **GitHub** | Submit the complete project repository |

---

## 4. Project Workflow

```
+---------------+     +------------------+     +---------------+     +----------------+
|  resume.txt   | --> |  main.py         | --> |  Gemini API   | --> |  JSON response |
+---------------+     +------------------+     +---------------+     +----------------+
        ^                     |                                                 |
        |                     v                                                 v
        |            validation + cleaning                              safe JSON parsing
        |                     |                                                 |
        |                     v                                                 v
        |            prompt built with resume text                 validate + fill empty values
        |                                                                        |
        +-----------------------------------------------------------------+     |
                                                                          v     |
                                          template.html + style.css <-- HTML generation
                                                                          |
                                                                          v
                                                                    portfolio.html
```

### Step-by-step flow

1. Place resume content inside `resume.txt`.
2. Run the Python program (`python main.py`).
3. Validate and clean the resume text (missing / empty / too short checks).
4. Create a structured prompt and send it to Gemini.
5. Receive portfolio content in JSON format.
6. Convert the JSON response into Python data.
7. Insert the data into an HTML template.
8. Save the final output as `portfolio.html`.
9. Open the portfolio in a browser and verify all information against the resume.

---

## 5. Project Structure

```
resume-portfolio-generator/
  main.py            # the complete pipeline (entry point)
  resume.txt         # sample input resume
  template.html      # HTML template with {{PLACEHOLDERS}}
  style.css          # CSS stylesheet used by portfolio.html
  requirements.txt   # Python dependencies
  README.md          # setup + run + testing documentation
  .gitignore         # ignores .env, __pycache__, .venv, etc.
  .env.example       # template for the local .env file
  portfolio.html     # generated output (sample included)
  tests/
    test_main.py     # pytest tests for all mandatory cases
```

---

## 6. Input Handling (`resume.txt`)

### Reading and validation

`main.py` reads `resume.txt` in UTF-8 and validates it before any API call:

| Condition | Behaviour |
| --- | --- |
| File missing | `InputError`: *"Resume file not found: ..."* |
| File empty / only blank lines | `InputError`: *"Resume file is empty or contains only blank lines."* |
| Cleaned text shorter than 80 characters | `InputError`: *"Resume is too short (N characters). Add at least 80 characters..."* |
| Valid content | Returns cleaned text and continues |

### Cleaning

The `clean_text()` function:

- Splits the file into lines.
- Strips leading/trailing spaces from each line.
- Collapses multiple internal spaces into one (`re.sub(r"\s+", " ", line)`).
- Removes blank lines entirely.
- Re-joins the remaining lines.

Example:

```
"   Hello    world\n\n\n   Python   \n\n"
        becomes
"Hello world\nPython"
```

This reduces noise sent to Gemini and keeps the prompt smaller and cleaner.

---

## 7. Gemini Integration

### API key

- The key is stored in a local `.env` file using the `python-dotenv` library.
- `get_api_key()` reads `GEMINI_API_KEY` from the environment.
- If it is missing, the program raises a `ConfigError` with clear instructions:
  copy `.env.example` to `.env` and add the key from Google AI Studio.
- **The real key is never in the source code and is ignored by Git** (`.gitignore`
  contains `.env`).

### Model

- The model is read from `GEMINI_MODEL` in `.env`.
- The default is `gemini-3.6-flash` (instructor-approved models can be set in
  `.env` without changing the code).

### API call

The current official Google GenAI SDK (`google-genai`) is used:

```python
client = genai.Client(api_key=api_key)
response = client.models.generate_content(
    model=model_name,
    contents=prompt,
    config=genai_types.GenerateContentConfig(
        temperature=0.4,
        response_mime_type="application/json",
    ),
)
```

Two important settings:

- `temperature=0.4` keeps output factual and reduces randomness.
- `response_mime_type="application/json"` forces Gemini to return valid JSON,
  which satisfies the "JSON only" requirement at the API level.

### Error handling

All API failures are caught and wrapped in a typed `GeminiError`. The program
prints a clean error message and exits with code `1` — it **never crashes** with a
traceback for expected errors.

---

## 8. Prompt Design

The prompt is built by `build_prompt(resume_text)` and strictly controls what
Gemini generates. It includes:

- The cleaned resume text.
- The instruction to use **only** information present in the resume.
- The instruction **not to invent** skills, experience, projects, achievements,
  companies, dates, or links.
- The instruction to use empty values (`""` / `[]`) for missing information.
- A defined JSON schema that Gemini must follow exactly.
- The requirement to return **JSON only**, with no markdown and no extra explanation.
- The requirement to keep the professional summary concise and factual.

The prompt acts as the contract between the program and the model. If the model
output is later checked and facts are wrong, the prompt is the first place to fix.

---

## 9. JSON Handling

### Requested schema

```json
{
  "name": "string",
  "headline": "string",
  "summary": "string",
  "skills": ["string"],
  "education": [
    { "degree": "string", "institution": "string", "year": "string" }
  ],
  "experience": [
    { "role": "string", "company": "string", "dates": "string", "description": "string" }
  ],
  "projects": [
    { "title": "string", "description": "string", "technologies": "string" }
  ],
  "achievements": ["string"],
  "contact": {
    "email": "string",
    "phone": "string",
    "linkedin": "string",
    "github": "string",
    "website": "string"
  }
}
```

### Safe parsing (`extract_json`)

Even though the API is asked for JSON, the program handles a messy response
gracefully. It tries, in order:

1. `json.loads` on the raw text.
2. Removing surrounding markdown fences (```` ```json ```` ... ```` ``` ````).
3. Slicing the text from the first `{` to the last `}`.
4. If all fail, it raises `ProjectError` (*"Invalid JSON received from Gemini"*)
   and stops safely.

### Normalisation (`validate_and_complete`)

After parsing, the data is normalised into a fixed Python structure:

- Text values are stripped and forced to strings (`as_string`).
- List values keep only non-empty strings (`as_string_list`).
- Record lists (education / experience / projects) keep only records that have at
  least one value and only the expected keys (`as_record_list`).
- Missing fields default to empty strings, empty lists, or an empty contact dict.
- If the JSON root is not an object, a clear error is raised.

This guarantees the rest of the program always works with a consistent structure,
no matter how Gemini responds.

---

## 10. HTML Generation

### Template and CSS separation

The brief requires a **separate HTML template and CSS file**, and that Gemini
output is **never manually pasted** into the final HTML. This project satisfies
both:

- `template.html` is the skeleton page with placeholders like `{{HEADER}}`,
  `{{SKILLS}}`, `{{PROJECTS}}`, etc., and links to `style.css`.
- `main.py` replaces each placeholder with the matching built section.
- `portfolio.html` is the final generated file, built only by Python.

### Hiding empty sections

Each section builder returns an empty string when there is no data, so the
corresponding placeholder becomes nothing. For example, if a resume has no
projects, the `{{PROJECTS}}` placeholder is replaced with an empty string and no
empty "Projects" box appears.

### Escaping

All text inserted into HTML is passed through `html.escape()`, preventing broken
pages or HTML/script injection from resume content (e.g. a resume containing
`<script>`).

### Generated sections

| Section | Source data | Rendered as |
| --- | --- | --- |
| Header | `name`, `headline` | Editorial banner: `// portfolio` tag, big serif name, italic headline |
| Professional Summary | `summary` | Paragraph with a burnt-orange accent bar |
| Skills | `skills` | Rough mono tags with dashed borders |
| Education | `education` | Timeline items (year / degree / institution) |
| Experience | `experience` | Timeline items (company · dates / role / description) |
| Projects | `projects` | Two-column cards with a mono tech line |
| Achievements | `achievements` | Numbered list (01, 02, ...) |
| Contact | `contact` | Underlined mono text links |

Contact fields are turned into proper links: `mailto:` for email, `tel:` for
phone, and `https://` for social links (a username without `http` gets the prefix
added automatically).

---

## 11. CSS (`style.css`)

The stylesheet gives the portfolio a hand-rolled, editorial identity instead of a
generic template look:

- A warm "paper" background (`#f6f1e7`) with a subtle dotted texture.
- A serif/mono type pairing (Georgia for names and headings, Consolas for dates,
  tags, and links) on top of a plain sans-serif body.
- A burnt-orange accent (`#d1492c`) with deep-green meta lines (`#2f7d6b`).
- **Hard offset shadows** (`6px 6px 0`) instead of soft AI-style glow shadows,
  giving the cards a flat, printed feel.
- A hand-drawn double underline under the name.
- Dashed skill tags, a dotted-timeline layout for experience/education, numbered
  achievements, and underlined contact links.
- A mobile media query and a print-friendly style block.

The generated `portfolio.html` links directly to `style.css`, so the page is
fully styled when opened in a browser.

---

## 12. Code Overview (`main.py`)

### Functions

| Function | Responsibility |
| --- | --- |
| `clean_text(text)` | Remove blank lines and extra spaces |
| `read_and_validate_resume(path)` | Read + validate `resume.txt` |
| `load_env()` | Load `.env` variables |
| `get_api_key()` | Return key or raise `ConfigError` |
| `build_prompt(resume_text)` | Build the controlled prompt |
| `call_gemini(prompt, api_key, model_name)` | Call the Gemini API, return text |
| `extract_json(raw)` | Safely parse JSON from the response |
| `as_string` / `as_string_list` / `as_record_list` | Normalise values |
| `validate_and_complete(data)` | Fill defaults, enforce structure |
| `build_*_section(...)` | Build each portfolio section's HTML |
| `build_html(data)` | Replace placeholders in `template.html` |
| `write_output(path, content)` | Save `portfolio.html` |
| `main(argv=None)` | CLI entry point, wires everything together |

### Typed errors

```
ProjectError  (base)
  ├── ConfigError     (missing API key / missing package)
  ├── InputError      (missing / empty / too-short resume)
  └── GeminiError     (API failure or empty response)
```

All expected failures are caught in `main()`, printed as `[error] ...`, and the
program exits with status `1`.

### CLI options

```
python main.py                     # normal run (resume.txt -> portfolio.html)
python main.py --demo              # use bundled sample data, no API key needed
python main.py --resume FILE       # different input file
python main.py --output FILE       # different output file
```

`--demo` is provided so the HTML pipeline can be tested on any computer, even
without a Gemini API key.

---

## 13. Testing

The mandatory test cases are implemented as `pytest` tests in
`tests/test_main.py`. Run with:

```bash
python -m pytest tests -q
```

**Result: 22 passed, 0 failed.**

| # | Test case | Expected behaviour | Implementation | Result |
| --- | --- | --- | --- | --- |
| 1 | Missing `resume.txt` | Clear error, stop safely | `test_read_missing_file_raises` | PASS |
| 2 | Empty resume file | Reject with useful message | `test_read_empty_file_rejected` | PASS |
| 3 | Very short resume | Reject with useful message | `test_read_short_file_rejected` | PASS |
| 4 | Valid resume | Generates `portfolio.html` | `test_build_html_includes_all_sections` | PASS |
| 5 | Resume with missing sections | Available sections only, nothing invented | `test_build_html_hides_empty_sections` | PASS |
| 6 | Missing API key | Configuration error | `test_get_api_key_missing` | PASS |
| 7 | API failure | Handled without crashing | `test_call_gemini_failure_is_wrapped` | PASS |
| 8 | Invalid JSON response | Clear error, stop safely | `test_extract_json_invalid_raises` | PASS |

Additional tests cover text cleaning, markdown-fence JSON, JSON slicing,
normalisation defaults, HTML escaping, empty Gemini responses, and end-to-end
CLI runs (`--demo`, missing file, missing key).

### Manual test results

| Action | Output |
| --- | --- |
| `python main.py --resume missing.txt` | `[error] Resume file not found: missing.txt` |
| empty `resume.txt` | `[error] Resume file is empty or contains only blank lines.` |
| short `resume.txt` (19 chars) | `[error] Resume is too short (19 characters)...` |
| valid `resume.txt`, no API key | `[error] GEMINI_API_KEY is missing...` |
| `python main.py --demo` | `[success] Portfolio written to ...\portfolio.html` |

---

## 14. Responsible AI & Privacy

- The sample resume contains **no** passwords, government ID numbers, or
  financial details.
- The real API key is stored only in `.env`, which is in `.gitignore`. It is
  never uploaded to GitHub and never appears in screenshots.
- The API key is used **only server-side in Python**. There is no browser-side
  JavaScript calling Gemini, so the key can never be exposed to page visitors.
- Every generated skill, project, date, company, achievement, and link must be
  checked against the original resume before submission.
- The README documents limitations and hallucination risks.

### Limitations & hallucination risks

1. **Invention risk**: Gemini can create facts that were not in the resume
   (e.g. a fake company or date). The prompt forbids this, but it is not 100%
   reliable.
2. **Paraphrasing**: The summary is rewritten, so wording differs from the resume.
3. **Summarisation loss**: Very long resumes may lose details.
4. **Non-determinism**: Re-running may give slightly different JSON.
5. **Dependency on input quality**: Noisy or poorly formatted resumes produce
   poorer portfolios.

**Mitigation**: strict prompt, `temperature=0.4`, forced JSON output, empty-value
defaults, and mandatory manual verification.

---

## 15. Three-Week Work Plan

| Week | Focus | Required work | Delivered |
| --- | --- | --- | --- |
| Week 1 | Python + Gemini setup | Repository + files, read/clean/validate `resume.txt`, API key, basic Gemini request, prompt design | Input pipeline + `build_prompt` + API call |
| Week 2 | JSON + portfolio generation | Structured JSON, safe parsing, `template.html` + `style.css`, automatic `portfolio.html` | Complete resume-to-portfolio workflow |
| Week 3 | Testing + submission | All test cases, verify generated info, README, screenshots, GitHub submission | Tested repository + generated portfolio |

---

## 16. AI Usage Log

| AI tool used | Prompt / request | What it generated | What was changed / corrected |
| --- | --- | --- | --- |
| ChatGPT (developer) | "Write a Python function that safely extracts JSON from a Gemini response" | JSON extraction snippet with markdown handling | Added fence stripping + `{...}` slicing fallbacks; reviewed edge cases; added tests |
| Gemini (code review) | "Review main.py for errors and missing error handling" | Suggestions for handling empty sections | Added `validate_and_complete` defaults and typed exceptions |
| Coding assistant (this repository) | "Implement the full project brief as a Python project" | Full pipeline, template, CSS, tests, docs | Every function reviewed, run end-to-end, covered by 22 passing tests; switched from the deprecated `google-generativeai` SDK to `google-genai` |

*Rule followed: all AI-generated code was reviewed, tested, and understood before
being included.*

---

## 17. Final Submission Checklist

- [ ] GitHub repository created and accessible
- [ ] `main.py`, `template.html`, `style.css`, `requirements.txt`, `.gitignore`,
      `.env.example` committed
- [ ] Safe sample `resume.txt` and generated `portfolio.html` included
- [ ] README with setup, run instructions, workflow, prompt design, limitations,
      and testing results
- [ ] Screenshots of the Python program output and the generated portfolio
- [ ] AI usage log recorded
- [ ] Final verification: every portfolio detail checked against the resume
- [ ] `.env` is NOT committed

---

## 18. How to Verify the Project (Definition of Completion)

A reviewer can:

1. Clone the GitHub repository.
2. Follow the README.
3. Add a valid Gemini API key to `.env`.
4. Run `python main.py`.
5. Generate `portfolio.html` from `resume.txt`.
6. Open `portfolio.html` in a browser.
7. Confirm every piece of content is supported by the original resume.

---

## 19. Optional Enhancements (future work)

- Additional CSS themes.
- A second HTML portfolio template.
- Extra sections: certifications, languages, interests.
- Deployment of the generated portfolio on a free hosting platform.
- A `--theme` CLI flag to switch styles.
- Export the structured JSON to a file for reuse.

---

*End of report. For quick setup and run instructions, see `README.md`.*
