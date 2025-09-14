from typing import List, Dict, Any
from models.models import JobPosting


def norm_workday(rows: List[Dict[str, Any]], company_hint: str) -> List[JobPosting]:
    out = []
    for r in rows:
        title = r.get("title") or r.get("title_facet") or ""
        # Some tenants provide 'locationsText'; else build from 'locations'
        loc = r.get("locationsText") or ", ".join([l.get("city","") for l in r.get("locations", []) if l.get("city")]) or None
        if not (loc and "india" in loc.lower()):
            # keep only India roles client-side
            continue
        external = r.get("externalPath") or r.get("externalPathTriggered")
        if external and external.startswith("/"):
            # Example tenant hostname; replace with the actual tenant domain you queried
            external = f"https://{company_hint}.myworkdayjobs.com{external}"
        out.append(JobPosting(
            source="workday",
            company=company_hint.capitalize(),
            title=title,
            location=loc,
            remote=None,
            tech_stack=_kw_stack(title + " " + (r.get("jobFamily","") or "")),
            compensation=None,
            url=external,
            job_id=str(r.get("bulletFields", {}).get("jobId") or r.get("id") or ""),
            description_snippet=title[:240]
        ))
    return out

def norm_netflix(rows: List[Dict[str, Any]]) -> List[JobPosting]:
    out = []
    for p in rows:
        loc = p.get("location") or ""
        if "india" not in loc.lower():
            continue
        out.append(JobPosting(
            source="netflix",
            company="Netflix",
            title=p.get("name",""),
            location=loc,
            remote=None,
            tech_stack=_kw_stack(p.get("name","")),
            compensation=None,
            url=p.get("canonicalPositionUrl"),
            job_id=str(p.get("ats_job_id") or p.get("id") or ""),
            description_snippet=p.get("name","")[:240],
        ))
    return out

def normalize_amazon_india(rows: List[Dict[str, Any]]) -> List[JobPosting]:
    out = []
    for r in rows:
        title = r.get("title") or r.get("job_title") or ""
        loc = r.get("normalized_location") or r.get("city_state_or_country") or r.get("location")
        path = r.get("job_path") or ""
        url = f"https://www.amazon.jobs{path}" if path else None
        tech = _kw_stack(f"{title} {r.get('basic_qualifications','')} {r.get('preferred_qualifications','')}")
        out.append(JobPosting(
            source="amazon",
            company=r.get("company_name") or "Amazon",
            title=title,
            location=loc,
            remote=None,
            tech_stack=tech,
            compensation=None,  # Amazon seldom posts comp openly
            url=url,
            job_id=str(r.get("id") or r.get("job_id") or ""),
            description_snippet=(r.get("description_summary") or r.get("description") or title)[:240],
        ))
    return out

def _kw_stack(text: str) -> List[str]:
    kws = [
        "python","flask","fastapi","django",
        "javascript","typescript","react","Next.js","node",
        "java","spring","kotlin","go","golang","rust","swift","swiftui",
        "aws","gcp","azure","docker","kubernetes","postgres","mysql","mongodb","redis","graphql",
    ]
    blob = text.lower()
    return [("Next.js" if k.lower()=="next.js" else k) for k in kws if k.lower() in blob]
