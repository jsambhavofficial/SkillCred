# AI-Assisted Resume Portfolio Generator

A simple Python application that converts resume text into a portfolio webpage.

`resume.txt` goes in -> the Python program sends it to the **Gemini API** ->
Gemini returns structured **JSON** -> Python generates **portfolio.html**.

Built for the **AIML GLA Bootcamp '26** student project brief. Group project,
5 members, 3 weeks.

---

## How it works

```
resume.txt  -->  main.py  -->  Gemini API  -->  JSON  -->  portfolio.html
                    |                                      (template.html + style.css)
                    +-- validation, cleaning, prompt design,
                        safe JSON parsing, empty-value defaults
```

## Project structure

```
resume-portfolio-generator/
  main.py          # main pipeline: read -> clean -> prompt -> Gemini -> JSON -> HTML
  resume.txt       # sample resume input (replace with your own)
  template.html    # HTML template (separate from generated output)
  style.css        # CSS stylesheet used by the generated portfolio
  requirements.txt # Python dependencies
  README.md        # this file
  .gitignore       # keeps .env and build files out of Git
  .env.example     # copy to .env and add your real API key
  portfolio.html   # generated output (already included as a sample)
  tests/           # pytest tests for all mandatory test cases
```

## Setup

1. **Install Python 3.10+** from <https://python.org>.
2. Clone or download this repository:
   ```bash
   git clone <your-repo-url>
   cd resume-portfolio-generator
   ```
3. Create a virtual environment (recommended) and install dependencies:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate        # Windows
   # source .venv/bin/activate   # macOS / Linux
   pip install -r requirements.txt
   ```
4. **Get a Gemini API key** from Google AI Studio:
   <https://aistudio.google.com/app/apikey>
5. Create your local `.env` file:
   ```bash
   copy .env.example .env        # Windows
   # cp .env.example .env        # macOS / Linux
   ```
   Open `.env`, replace `your_gemini_api_key_here` with your real key, and set the
   model approved by your instructor (`GEMINI_MODEL`).
   > **Never commit the `.env` file.** It is already in `.gitignore`.

## Running the program

Put your resume in `resume.txt`, then run:

```bash
python main.py
```

Successful output:

```
[info] Resume loaded and cleaned (1234 characters).
[info] Calling Gemini model 'gemini-3.6-flash'...
[info] Response received. Parsing JSON...
[success] Portfolio written to C:\...\portfolio.html
[tip] Open the file in a browser and verify every detail against the original resume.
```

Open `portfolio.html` in a browser and **verify every detail against `resume.txt`**.

### Testing without an API key

```bash
python main.py --demo
```

`--demo` builds `portfolio.html` from bundled sample data (no Gemini call), so the
HTML pipeline can be tested on any computer.

### Extra options

```bash
python main.py --resume my_resume.txt      # use a different input file
python main.py --output my_portfolio.html  # save output somewhere else
```

## The prompt design

The prompt in `main.py` (`build_prompt`) strictly controls Gemini:

- Uses **only** information present in the resume.
- **Never invents** skills, experience, projects, achievements, companies, dates, or links.
- Uses **empty values** for missing information.
- Requests **valid JSON only** (no markdown, no extra text).
- Keeps the professional summary concise and factual.
- The API call also uses `response_mime_type="application/json"` for guaranteed JSON output.

## JSON schema requested from Gemini

```json
{
  "name": "string",
  "headline": "string",
  "summary": "string",
  "skills": ["string"],
  "education": [{"degree": "string", "institution": "string", "year": "string"}],
  "experience": [{"role": "string", "company": "string", "dates": "string", "description": "string"}],
  "projects": [{"title": "string", "description": "string", "technologies": "string"}],
  "achievements": ["string"],
  "contact": {"email": "string", "phone": "string", "linkedin": "string", "github": "string", "website": "string"}
}
```

## Portfolio sections

Name, Headline, Professional Summary, Skills, Education, Experience, Projects,
Achievements, and Contact & Links. **Empty sections are automatically hidden**
in the generated page.

## Testing

Run the full test suite:

```bash
python -m pytest tests -q
```

Results of the mandatory test cases (all pass):

| Test case                        | Expected behaviour                                  | Result |
| -------------------------------- | --------------------------------------------------- | ------ |
| Missing `resume.txt`             | Clear error, stops safely                           | PASS   |
| Empty or very short resume       | Rejected with a useful message                      | PASS   |
| Valid resume                     | `portfolio.html` generated successfully            | PASS   |
| Resume with missing sections     | Available sections only, nothing invented           | PASS   |
| Missing API key                  | Configuration error shown                           | PASS   |
| API failure                      | Handled without crashing                            | PASS   |
| Invalid JSON response            | Clear error, stops safely                           | PASS   |

## Responsible AI & privacy

- Do **not** put passwords, ID numbers, financial details, or other sensitive data
  in the resume used for testing.
- Never upload the real API key to GitHub or show it in screenshots.
- The API key is only read from `.env` server-side in Python; it is never exposed
  in browser-side JavaScript.
- **Every generated claim must be checked against the original resume.** Gemini
  output is a draft.

### Limitations & hallucination risks

- Gemini can **invent** or slightly change facts (skills, companies, dates, links).
  The prompt reduces this, but cannot fully prevent it.
- Summaries are paraphrases, so wording may differ from the resume.
- Long or noisy resumes may be summarized imperfectly.
- No AI system is fully deterministic; the same resume may produce slightly
  different output on repeated runs.
- Manual verification before submission is **required**.

## AI usage log

| AI tool used           | Prompt / request                       | What it generated                    | Changes made before using it                                   |
| ---------------------- | -------------------------------------- | ------------------------------------ | ------------------------------------------------------------- |
| ChatGPT (developer)    | "Write a Python function that safely extracts JSON from a Gemini response" | JSON extraction with markdown handling | Added the fence-stripping and `{...}` slicing fallbacks; reviewed edge cases and added tests |
| Gemini (code review)   | "Review main.py for errors and missing error handling" | Suggestions for empty-section handling | Wrapped all failures in typed exceptions; added `validate_and_complete` defaults |
| Coding assistant (this repo) | "Implement the full brief as a Python project" | Full pipeline code, template, CSS, tests | Every function reviewed, manually tested end-to-end, and covered by 22 passing tests |

*Keep this table updated as you continue developing.*

## Final verification checklist

- [ ] `python main.py` runs and prints `[success]`
- [ ] `portfolio.html` opens in a browser and is styled correctly
- [ ] Every skill, project, company, date, achievement, and link in the page is
      present in `resume.txt`
- [ ] `.env` is not committed (check with `git status`)
- [ ] `python -m pytest tests -q` passes

## License

Free to use for the AIML GLA Bootcamp '26 submission.
