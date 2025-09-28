# Job-Searcher Backend (India Focus)

Aggregates public job listings from **Amazon India**, **Workday** tenants (e.g., **PwC India**), and **Netflix (Eightfold)**, normalizes them into a common schema, and (optionally) validates the response using the **OpenAI Agents SDK** (strict structured output). Exposes a simple **Flask** API your **Next.js** or **SwiftUI** app can consume.

---

## Features

* ⚡️ Async fetching with `httpx` (concurrent providers)
* 🧱 Typed models via **Pydantic** (`JobPosting`, `Compensation`)
* ✅ Optional strict schema enforcement using **Agents SDK** (`output_type=List[JobPosting]`)
* 🔎 Simple query filters (`q`, `location`, `city`)
* 🌐 CORS enabled for easy frontend dev
* 📜 Built-in **OpenAPI** spec + **Swagger UI** (`/docs`)

---

## Quickstart

```bash
git clone https://github.com/abhinavgo1000/Job-Searcher-Backend.git
cd Job-Searcher-Backend

python -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# (optional) serve docs at /docs
pip install pyyaml flask-swagger-ui

python app.py
# → http://localhost:5057
```

Test it:

```
GET http://localhost:5057/jobs?q=Full%20Stack&strict=false
GET http://localhost:5057/job-insights?position=Full%20Stack&companies=deloitte,google&years_experience=8&remote=true
```

---

## API

### `GET /jobs`

**Query parameters**

| Name              | Type    |                                                    Default | Description                                                                                                                                      |
| ----------------- | ------- | ---------------------------------------------------------: | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| `q`               | string  |                                               `Full Stack` | Keyword(s) (any-token match).                                                                                                                    |
| `location`        | string  |                                                          — | Extra substring filter on location after normalization.                                                                                          |
| `city`            | string  |                                                          — | Narrows **Amazon India** results server-side (e.g., `Bengaluru`).                                                                                |
| `strict`          | boolean |                                                     `true` | If `true`, runs the OpenAI **Agents** “enforcer” for strictly typed output. If `false`, returns raw normalized results (faster, no OpenAI call). |
| `include_amazon`  | boolean |                                                     `true` | Toggle Amazon provider.                                                                                                                          |
| `include_netflix` | boolean |                                                     `true` | Toggle Netflix (Eightfold) provider.                                                                                                             |
| `workday`         | string  | `pwc.wd3.myworkdayjobs.com:Global_Experienced_Careers:pwc` | Comma-sep list of Workday targets as `host:site:company_hint`. Example: `pwc.wd3.myworkdayjobs.com:Global_Experienced_Careers:pwc`.              |

**Examples**

```
/jobs?q=Full%20Stack
/jobs?q=Full%20Stack&city=Bengaluru&include_netflix=false&strict=false
/jobs?q=Full%20Stack&workday=pwc.wd3.myworkdayjobs.com:Global_Experienced_Careers:pwc
```

**Response**: `200 OK` → `JobPosting[]` (see schema)

---

### `POST /save-job`

Save a job posting to the database.

**Request body example:**
```json
{
    "id": "a3b4d9e12f0c4b8a",
    "source": "amazon",
    "company": "Amazon",
    "title": "Full Stack Engineer, Prime Video",
    "location": "Bengaluru, KA, IN",
    "remote": false,
    "tech_stack": [
      "javascript",
      "typescript",
      "react",
      "node",
      "aws"
    ],
    "compensation": null,
    "url": "https://www.amazon.jobs/en/jobs/123456/full-stack-engineer",
    "job_id": "123456",
    "description_snippet": "Design and build scalable full-stack services…"
  }
```

**Response:** `201 Created` → The saved `JobInsights` object.

---

### `GET /saved-jobs`

List all saved job postings.

**Response:** `200 OK` → Array of `JobPosting` objects.

---

### `DELETE /delete-jobs/{job_id}`

Delete a saved job posting by its database ID.

**Response:**  
- `200 OK` → `{ "deleted_count": 1 }` if successful  
- `404 Not Found` or `400 Bad Request` if the ID is invalid or not found

---

## Insight API

### `GET /jobs`

**Query parameters**

| Name              | Type    |                                                    Default | Description                                                                                                                                      |
| ----------------- | ------- | ---------------------------------------------------------: | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| `position`               | string  |                                               `Full Stack` | Keyword(s) (any-token match).                                                                                                                    |
| `company`        | string  |                                                          — | String list for companies to search.                                                                                          |
| `years_experience`            | int  |                                                          — | Number of years of experience.                                                                                |
| `remote`          | boolean |                                                     `true` | If `true`, performs the search based on the available remote roles. |

**Examples**

```
/job-insights?position=Full%20Stack&companies=deloitte,google&years_experience=8&remote=true
```

**Response**: `200 OK` → `JobInsights[]` (see schema)

---

### `POST /save-insight`

Save a job insight to the database.

**Request body example:**
```json
{
  "summary": "Strong backend and cloud skills required.",
  "skills": [
    {
      "name": "Python",
      "description": "Used for backend development.",
      "proficiency_level": "Expert",
      "category": "Backend"
    },
    {
      "name": "AWS",
      "description": "Cloud deployment and management.",
      "proficiency_level": "Intermediate",
      "category": "Cloud"
    }
  ],
  "feedback": "Ensure hands-on experience with cloud platforms."
}
```

**Response:** `201 Created` → The saved `JobInsights` object.

---

### `GET /saved-insights`

List all saved job insights.

**Response:** `200 OK` → Array of `JobInsights` objects.

---

### `DELETE /delete-insights/{insight_id}`

Delete a saved job insight by its database ID.

**Response:**  
- `200 OK` → `{ "deleted_count": 1 }` if successful  
- `404 Not Found` or `400 Bad Request` if the ID is invalid or not found

---

## Example Insight API Calls

* **Save an insight:**
  ```
  POST http://localhost:5057/save-insight
  Content-Type: application/json

  { ...see above example... }
  ```

* **List saved insights:**
  ```
  GET http://localhost:5057/saved-insights
  ```

* **Delete an insight:**
  ```
  DELETE http://localhost:5057/delete-insights/6510e1e6e1b2c8e1f0a1b2c3
  ```

---

## Data Model (Insight)

```python
class SkillDetail(BaseModel):
    name: str
    description: str
    proficiency_level: str
    category: Optional[str] = None

class JobInsights(BaseModel):
    summary: str
    skills: List[SkillDetail]
    feedback: Optional[str] = None
```

## Data Model (summary)

```py
# models.py
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, model_validator
from uuid import uuid4
import hashlib

class Compensation(BaseModel):
    currency: Optional[str] = None
    min: Optional[float] = None
    max: Optional[float] = None
    period: Optional[Literal["hour","day","month","year","total"]] = None
    notes: Optional[str] = None

class JobPosting(BaseModel):
    id: Optional[str] = Field(default=None, description="Stable id or random fallback")
    source: str
    company: str
    title: str
    location: Optional[str] = None
    remote: Optional[bool] = None
    tech_stack: List[str] = Field(default_factory=list)
    compensation: Optional[Compensation] = None
    url: Optional[str] = None        # keep as str (not HttpUrl) for OpenAI schema
    job_id: Optional[str] = None     # provider-native id
    description_snippet: Optional[str] = None

    @model_validator(mode="after")
    def _ensure_id(self):
        if not self.id:
            base = f"{self.source}|{self.job_id or ''}|{self.url or ''}"
            self.id = hashlib.sha256(base.encode()).hexdigest()[:16] if base.strip("|") else uuid4().hex
        return self
```

---

## Project Structure

```
.
├── app.py                         # Flask API & aggregation
├── helpers/                       # Helper tools for web search, data scraping and emailing
├── models/                        # Pydantic models
├── providers/                     # Async providers for Amazon, Netflix, and Workday
├── normalizers                    # Amazon, Workday & Netflix → JobPosting[]
├── openapi.yaml                   # OpenAPI spec (served at /openapi.json)
├── requirements.txt
└── README.md
```

---

## Providers

### Amazon India

* Endpoint: `https://www.amazon.jobs/en/search.json`
* No auth; send `Accept: application/json`, a browsery `User-Agent`, `Referer`.
* Provider includes a broad India filter; optionally pass `city=Bengaluru`.

### Workday (e.g., PwC India)

* POST JSON to: `https://{host}/wday/cxs/{tenant}/{site}/jobs`
* Example host/site: `pwc.wd3.myworkdayjobs.com : Global_Experienced_Careers`
* We send `appliedFacets.locations=["locationCountry:country:IN"]` to filter to India.
* `site` is **case-sensitive**; host must include the `wdN` segment.

### Netflix (Eightfold)

* Careers microsite injects a large JSON payload; provider extracts and normalizes.
* We then filter to India roles in the normalizer.

---

## OpenAPI & Docs

* OpenAPI YAML lives at `openapi.yaml`
* The app serves:

  * `GET /openapi.json` – JSON version of the spec
  * `GET /openapi.yaml` – raw YAML (optional)
  * `GET /docs` – Swagger UI

If you haven’t yet wired docs, add:

```bash
pip install pyyaml flask-swagger-ui
```

Then in `main.py`:

```py
import json, yaml
from pathlib import Path
from flask_swagger_ui import get_swaggerui_blueprint

OPENAPI_PATH = Path(__file__).parent / "openapi.yaml"
SWAGGER_URL = "/docs"
OPENAPI_URL = "/openapi.json"

@app.get("/openapi.json")
def openapi_json():
    return app.response_class(
        response=json.dumps(yaml.safe_load(OPENAPI_PATH.read_text())),
        status=200,
        mimetype="application/json",
    )

swaggerui_blueprint = get_swaggerui_blueprint(SWAGGER_URL, OPENAPI_URL, config={"app_name": "Job Searcher Backend"})
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)
```

---

## Requirements

```txt
# --- Web API ---
Flask==3.1.2
flask-cors==6.0.1
pymongo==4.15.1
certifi==2025.8.3
requests==2.32.5
beautifulsoup4==4.14.0
selenium==4.35.0
scrapy==2.13.3
sendgrid==6.12.5
python-dotenv
flask-swagger-ui==5.21.0

# --- Async HTTP client for providers (Amazon / Workday / Netflix) ---
httpx==0.28.1

# --- Data models / validation ---
pydantic==2.11.9
typing-extensions>=4.12.2
pyyaml==6.0.3

# --- OpenAI Agents SDK (for structured/typed agent output) ---
openai-agents>=0.3.0

# --- (Optional) ASGI server if you switch to async Flask/FastAPI ---
# uvicorn[standard]==0.30.0
```

Install:

```bash
pip install -r requirements.txt
```

---

## Example Calls

* **Default (strict on):**

  ```
  /jobs?q=Full%20Stack
  ```
* **Amazon + PwC, Netflix off, raw (strict off):**

  ```
  /jobs?q=Full%20Stack&city=Bengaluru&include_netflix=false&workday=pwc.wd3.myworkdayjobs.com:Global_Experienced_Careers:pwc&strict=false
  ```

  * ** (Insights) Full Stack remote roles in Deloitte and Google:**

  ```
  /job-insights?position=Full%20Stack&companies=deloitte,google&years_experience=8&remote=true
  ```

---

## Troubleshooting

* **Empty `[]`**

  * Try `strict=false` to bypass the Agent and see raw results.
  * Check logs — each provider logs row counts and errors.
  * Loosen filters (remove `city` / `location`).

* **Workday `400 Bad Request`**

  * Verify **host** (includes `wdN`) and exact **site** string.
  * Read the logged body — Workday often tells you what’s wrong.
  * Start with: `pwc.wd3.myworkdayjobs.com:Global_Experienced_Careers:pwc`.

* **Agents SDK / event loop**

  * In sync Flask routes, wrap calls with `asyncio.run(...)`.
  * Use `Runner.run(...)` (not `agent.run`).

* **Schema error mentioning `"format":"uri"`**

  * Ensure `JobPosting.url` is `str`, not `HttpUrl`.

---

## Roadmap

* Add more India-specific providers (Google/Apple/Meta portals, Oracle Cloud Recruiting, SuccessFactors).
* Redis cache + de-dup across runs.
* Pagination (`limit`, `offset`) and sorting.
* Unit tests for providers/normalizers.

---

## License

MIT (adjust as needed).
