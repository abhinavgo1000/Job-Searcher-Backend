import httpx
from typing import List, Dict, Any
import logging
log = logging.getLogger(__name__)

async def fetch_workday_jobs(
    host: str,
    site: str,
    search_text: str = "",
    limit: int = 50,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """
    host: full Workday host, e.g. 'pwc.wd3.myworkdayjobs.com'
    site: external site name, e.g. 'Global_Experienced_Careers'
    Filters to India on the server via facets.
    """
    tenant = host.split(".", 1)[0]  # 'pwc'
    url = f"https://{host}/wday/cxs/{tenant}/{site}/jobs"

    payload = {
        "appliedFacets": {
            # Country facet: locationCountry:<type>:<ISO2>
            "locations": ["locationCountry:country:IN"]
        },
        "limit": limit,
        "offset": offset,
        "searchText": search_text or ""
    }

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0",
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(url, json=payload, headers=headers)
        if resp.status_code >= 400:
            log.error(
                "Workday fetch failed: %s %s — %s %s",
                url, site, resp.status_code, resp.text[:500]
            )
            resp.raise_for_status()
        data = resp.json()
        rows = data.get("jobPostings", []) or []
        return rows
