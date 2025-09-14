from __future__ import annotations

from typing import List, Dict, Any, Optional
import httpx
import logging

log = logging.getLogger(__name__)

AMZ_BASE = "https://www.amazon.jobs/en/search.json"  # note /en/

HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome Safari",
    "Referer": "https://www.amazon.jobs/en/search",
}

async def _fetch_page(
    client: httpx.AsyncClient,
    query: str,
    loc_query: Optional[str],
    result_limit: int,
    offset: int,
) -> List[Dict[str, Any]]:
    params = {
        "base_query": query or "",
        "loc_query": (loc_query or "India"),
        "result_limit": result_limit,
        "offset": offset,
        "facets[]": [
            "location","business_category","category","schedule_type_id",
            "employee_class","normalized_location","job_function_id",
        ],
        "sort": "recent",
    }
    r = await client.get(AMZ_BASE, params=params, headers=HEADERS, follow_redirects=True)
    try:
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        log.exception("Amazon page fetch failed: %s %s", r.status_code, r.text[:400])
        raise
    return data.get("jobs", []) or []

def _is_india(rec: Dict[str, Any]) -> bool:
    loc = (rec.get("normalized_location")
           or rec.get("city_state_or_country")
           or rec.get("location") or "")
    s = str(loc).lower()
    # accept common forms
    return any(token in s for token in ("india", ", in", " ind", "(in)", " in "))

def _city_matches(rec: Dict[str, Any], city: str | None) -> bool:
    if not city:
        return True
    loc = (rec.get("normalized_location")
           or rec.get("city_state_or_country")
           or rec.get("location") or "")
    return city.lower() in str(loc).lower()

async def fetch_amazon_india(
    query: str = "Full Stack",
    loc_query: Optional[str] = None,
    page_size: int = 50,
    max_pages: int = 5,
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    async with httpx.AsyncClient(timeout=30) as client:
        for page in range(max_pages):
            offset = page * page_size
            page_rows = await _fetch_page(client, query, loc_query, page_size, offset)
            if not page_rows:
                break
            rows.extend(page_rows)
            if len(page_rows) < page_size:
                break

    rows = [r for r in rows if _is_india(r)]
    if loc_query:
        rows = [r for r in rows if _city_matches(r, loc_query)]
    return rows
