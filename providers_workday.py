import httpx
from typing import List, Dict, Any

async def fetch_workday_jobs(tenant: str, site: str, search_text: str = "", limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
    """
    Generic Workday 'External Career Site' fetcher.
    NOTE: Different tenants expose different facets; we keep payload minimal and filter client-side for India.
    """
    url = f"https://{tenant}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs"
    payload = {"appliedFacets": {}, "limit": limit, "offset": offset, "searchText": search_text}
    headers = {"Accept": "application/json", "Content-Type": "application/json", "Origin": f"https://{tenant}.myworkdayjobs.com"}
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(url, json=payload, headers=headers)
        r.raise_for_status()
        data = r.json()
    return data.get("jobPostings", [])

