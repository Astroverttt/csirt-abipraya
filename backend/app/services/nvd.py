"""
Async NVD (National Vulnerability Database) API client.

Handles rate-limiting and caching to respect NVD's API limits.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

import httpx

from ..config import settings

logger = logging.getLogger("patchops.nvd")

NVD_BASE = "https://services.nvd.nist.gov/rest/json/cves/2.0"

# ── In-memory cache ──────────────────────────────────────────────────────────
_cache: Optional[Dict[str, Any]] = None
_cache_ts: float = 0
CACHE_TTL = 3600  # 1 hour


def _get_cached() -> Optional[list]:
    global _cache, _cache_ts
    if _cache and (time.time() - _cache_ts) < CACHE_TTL:
        return _cache["data"]
    return None


def _set_cached(data: list) -> None:
    global _cache, _cache_ts
    _cache = {"data": data}
    _cache_ts = time.time()


def clear_cache() -> None:
    global _cache, _cache_ts
    _cache = None
    _cache_ts = 0


async def fetch_recent_cves(keywords: List[str], days_back: int = 7) -> list:
    """
    Fetch recent CVEs from NVD for a list of package keywords.
    Rate-limited to ~5 requests per 30 seconds.
    """
    cached = _get_cached()
    if cached is not None:
        return cached

    from datetime import datetime, timedelta, timezone

    now = datetime.now(timezone.utc)
    start_date = now - timedelta(days=days_back)

    pub_start = start_date.isoformat().replace("+00:00", "")
    pub_end = now.isoformat().replace("+00:00", "")

    all_cves: List[Dict[str, Any]] = []
    seen: set = set()

    limited_keywords = keywords[:10]
    headers = {}
    if settings.NVD_API_KEY:
        headers["apiKey"] = settings.NVD_API_KEY

    async with httpx.AsyncClient(timeout=httpx.Timeout(15.0)) as client:
        for i, keyword in enumerate(limited_keywords):
            try:
                response = await client.get(
                    NVD_BASE,
                    params={
                        "keywordSearch": keyword,
                        "pubStartDate": pub_start,
                        "pubEndDate": pub_end,
                        "noRejected": "",
                        "resultsPerPage": 20,
                    },
                    headers=headers,
                )
                response.raise_for_status()
                vulns = response.json().get("vulnerabilities", [])

                for item in vulns:
                    cve = item.get("cve", {})
                    cve_id = cve.get("id")
                    if not cve_id or cve_id in seen:
                        continue
                    seen.add(cve_id)

                    cvss_v31 = (cve.get("metrics", {}).get("cvssMetricV31") or [{}])[0].get("cvssData", {})
                    cvss_v30 = (cve.get("metrics", {}).get("cvssMetricV30") or [{}])[0].get("cvssData", {})
                    cvss_data = cvss_v31 or cvss_v30

                    descriptions = cve.get("descriptions", [])
                    en_desc = next((d["value"] for d in descriptions if d.get("lang") == "en"), "")

                    all_cves.append({
                        "id": cve_id,
                        "published": cve.get("published"),
                        "description": en_desc,
                        "baseScore": cvss_data.get("baseScore"),
                        "baseSeverity": cvss_data.get("baseSeverity"),
                        "matchedKeyword": keyword,
                        "references": [r["url"] for r in (cve.get("references") or [])[:2]],
                    })
            except Exception as e:
                logger.warning("NVD query failed for '%s': %s", keyword, e)

            # Rate limiting
            if i < len(limited_keywords) - 1:
                await asyncio.sleep(6.5)

    all_cves.sort(key=lambda x: x.get("baseScore") or 0, reverse=True)
    _set_cached(all_cves)
    return all_cves
