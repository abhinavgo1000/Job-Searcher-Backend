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

Then in `app.py`:

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
Flask==3.0.3
flask-cors==4.0.0
httpx==0.27.0
pydantic==2.8.2
typing-extensions>=4.12.2
openai-agents>=0.2.0
# docs (optional)
pyyaml==6.0.2
flask-swagger-ui==4.11.1
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
