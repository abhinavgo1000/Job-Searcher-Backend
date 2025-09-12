import httpx, re, json
from typing import List, Dict, Any

# Captures the big JSON blob embedded on the search page
_POSITIONS_RE = re.compile(r'("positions"\s*:\s*\[.*?])', re.DOTALL)

async def fetch_netflix_positions() -> List[Dict[str, Any]]:
    url = "https://explore.jobs.netflix.net/careers"
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(url)
        r.raise_for_status()
        txt = r.text
    m = _POSITIONS_RE.search(txt)
    if not m:
        return []
    # Build a minimal JSON document to parse
    blob = json.loads("{"+m.group(1)+"}")
    return blob.get("positions", [])

