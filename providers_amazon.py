from typing import List, Dict, Any, Optional
import httpx

AMZ_BASE = "https://www.amazon.jobs/search.json"

async def _fetch_page(
    client: httpx.AsyncClient,
    query: str,
    loc_query: Optional[str],
    result_limit: int,
    offset: int,
) -> List[Dict[str, Any]]:
    params = {
        "base_query": query or "",
        "loc_query": loc_query or "India",
        "result_limit": result_limit,
        "offset": offset,
        # These mirror the site’s filters; harmless if the API ignores extras.
        "facets[]": [
            "location",
            "business_category",
            "category",
            "schedule_type_id",
            "employee_class",
            "normalized_location",
            "job_function_id",
        ],
        "sort": "recent",
    }
    r = await client.get(AMZ_BASE, params=params, headers={"Accept": "application/json"})
    r.raise_for_status()
    data = r.json()
    return data.get("jobs", []) or []

async def fetch_amazon_india(
    query: str = "Full Stack",
    loc_query: Optional[str] = None,    # e.g., "Bengaluru" to narrow; defaults to India-wide
    page_size: int = 50,
    max_pages: int = 5,                 # safety cap
) -> List[Dict[str, Any]]:
    """
    Fetches Amazon jobs and returns the raw 'jobs' objects from amazon.jobs.
    We paginate with offset until no items, or we hit max_pages.
    """
    rows: List[Dict[str, Any]] = []
    async with httpx.AsyncClient(timeout=30) as client:
        for page in range(max_pages):
            offset = page * page_size
            page_rows = await _fetch_page(client, query, loc_query, page_size, offset)
            if not page_rows:
                break
            rows.extend(page_rows)
            # If fewer than page_size, likely the last page
            if len(page_rows) < page_size:
                break
    # Client-side India filter, just in case
    def in_india(rec: Dict[str, Any]) -> bool:
        loc = (rec.get("normalized_location") or rec.get("city_state_or_country") or rec.get("location") or "")
        return "india" in str(loc).lower()
    return [r for r in rows if in_india(r)]
