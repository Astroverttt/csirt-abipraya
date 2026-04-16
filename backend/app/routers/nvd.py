"""
NVD router — proxies CVE lookups through the backend.
"""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends

from ..dependencies import get_current_session
from ..models.schemas import NVDSearchRequest
from ..services import nvd

router = APIRouter(prefix="/api/nvd", tags=["nvd"])


@router.post("/cves")
async def search_cves(
    body: NVDSearchRequest,
    _session: Dict[str, Any] = Depends(get_current_session),
):
    """Search NVD for recent CVEs by package keywords."""
    return await nvd.fetch_recent_cves(body.keywords, body.days_back)


@router.post("/clear-cache")
async def clear_nvd_cache(
    _session: Dict[str, Any] = Depends(get_current_session),
):
    """Clear the NVD response cache."""
    nvd.clear_cache()
    return {"message": "NVD cache cleared"}
