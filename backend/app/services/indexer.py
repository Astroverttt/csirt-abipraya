"""
Async Wazuh Indexer (Elasticsearch) client.

All Elasticsearch queries are proxied through the backend so that
Indexer credentials never reach the client browser.
"""

from __future__ import annotations

import base64
import logging
from typing import Any, Dict, Optional

import httpx

from ..config import settings

logger = logging.getLogger("patchops.indexer")


def _client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=settings.INDEXER_URL,
        verify=False if not settings.INDEXER_VERIFY_SSL else True,
        timeout=httpx.Timeout(15.0),
    )


def _auth_header(username: Optional[str] = None, password: Optional[str] = None) -> Dict[str, str]:
    # Prioritize settings if provided in .env, otherwise fallback to passed credentials
    u = settings.INDEXER_USERNAME or username
    p = settings.INDEXER_PASSWORD or password
    
    if not u or not p:
        return {}
        
    creds = base64.b64encode(f"{u}:{p}".encode()).decode()
    return {"Authorization": f"Basic {creds}"}


async def search(
    index: str,
    query: Dict[str, Any],
    username: Optional[str] = None,
    password: Optional[str] = None,
) -> Dict[str, Any]:
    """Execute an Elasticsearch search query."""
    async with _client() as client:
        response = await client.post(
            f"/{index}/_search",
            json=query,
            headers={
                **_auth_header(username, password),
                "Content-Type": "application/json",
            },
        )
        response.raise_for_status()
        return response.json()


async def get_alert_history_summary(username: Optional[str] = None, password: Optional[str] = None) -> Dict[str, Any]:
    """
    Fetch aggregated alert summary for all agents.
    Replicates the frontend's getAllAlertHistorySum query.
    """
    query = {
        "query": {
            "bool": {
                "should": [
                    {
                        "bool": {
                            "must": [
                                {"term": {"rule.groups": "vulnerability-detector"}},
                                {"terms": {"data.vulnerability.severity": ["Critical", "High"]}},
                            ]
                        }
                    },
                    {"range": {"rule.level": {"gte": 12}}},
                ],
                "minimum_should_match": 1,
            }
        },
        "aggs": {
            "agents": {
                "terms": {"field": "agent.id", "size": 1000},
                "aggs": {
                    "severity": {
                        "filters": {
                            "filters": {
                                "Critical": {
                                    "bool": {
                                        "should": [
                                            {"term": {"data.vulnerability.severity": "Critical"}},
                                            {"term": {"rule.level": 15}},
                                        ],
                                        "minimum_should_match": 1,
                                    }
                                },
                                "High": {
                                    "bool": {
                                        "should": [
                                            {"term": {"data.vulnerability.severity": "High"}},
                                            {"range": {"rule.level": {"gte": 12, "lte": 14}}},
                                        ],
                                        "minimum_should_match": 1,
                                    }
                                },
                            }
                        }
                    }
                },
            }
        },
        "size": 0,
    }

    try:
        data = await search("wazuh-alerts-*", query, username, password)
        buckets = data.get("aggregations", {}).get("agents", {}).get("buckets", [])

        result = {}
        for bucket in buckets:
            crit = bucket["severity"]["buckets"]["Critical"]["doc_count"]
            high = bucket["severity"]["buckets"]["High"]["doc_count"]
            result[bucket["key"]] = {
                "total": bucket["doc_count"],
                "critical": crit,
                "high": high,
            }
        return result
    except Exception as e:
        logger.warning("Indexer alert summary failed: %s", e)
        return {}


async def get_alert_history_details(
    agent_id: str, username: Optional[str] = None, password: Optional[str] = None
) -> list:
    """Fetch detailed alert history for a specific agent."""
    query = {
        "query": {
            "bool": {
                "must": [{"term": {"agent.id": agent_id}}],
                "should": [
                    {
                        "bool": {
                            "must": [
                                {"term": {"rule.groups": "vulnerability-detector"}},
                                {"terms": {"data.vulnerability.severity": ["Critical", "High"]}},
                            ]
                        }
                    },
                    {"range": {"rule.level": {"gte": 12}}},
                ],
                "minimum_should_match": 1,
            }
        },
        "sort": [{"timestamp": {"order": "desc"}}],
        "size": 500,
    }

    data = await search("wazuh-alerts-*", query, username, password)
    return data.get("hits", {}).get("hits", [])


async def get_all_alert_history_details(
    username: Optional[str] = None, password: Optional[str] = None
) -> list:
    """Fetch detailed alert history for ALL agents in the last 24h with rule level >= 12."""
    query = {
        "query": {
            "bool": {
                "must": [
                    {"range": {"rule.level": {"gte": 12}}},
                    {"range": {"timestamp": {"gte": "now-24h"}}},
                ],
            }
        },
        "sort": [{"timestamp": {"order": "desc"}}],
        "size": 1000, # Reduced size as we only care about recent alerts
    }

    try:
        data = await search("wazuh-alerts-*", query, username, password)
        return data.get("hits", {}).get("hits", [])
    except Exception as e:
        logger.warning("All alert history details fetch failed: %s", e)
        return []


async def get_active_vulnerabilities(
    agent_id: str, username: Optional[str] = None, password: Optional[str] = None
) -> list:
    """Fetch active/current vulnerabilities from Wazuh States index."""
    query = {
        "query": {"bool": {"must": [{"term": {"agent.id": agent_id}}]}},
        "size": 10000,
    }

    try:
        data = await search("wazuh-states-vulnerabilities-*", query, username, password)
        hits = data.get("hits", {}).get("hits", [])
        return [
            {
                "cve": h["_source"].get("vulnerability", {}).get("id"),
                "name": h["_source"].get("package", {}).get("name"),
                "version": h["_source"].get("package", {}).get("version"),
                "severity": h["_source"].get("vulnerability", {}).get("severity", "Unknown"),
                "cvss": h["_source"].get("vulnerability", {}).get("score", {}).get("base"),
                "condition": h["_source"].get("vulnerability", {}).get("scanner", {}).get("condition"),
                "title": h["_source"].get("vulnerability", {}).get("title")
                or h["_source"].get("vulnerability", {}).get("id"),
            }
            for h in hits
        ]
    except Exception as e:
        logger.warning("Active vulnerabilities fetch failed: %s", e)
        return []


async def get_all_active_vulnerabilities(
    username: Optional[str] = None, password: Optional[str] = None
) -> Dict[str, list]:
    """Fetch active/current vulnerabilities for ALL agents in one bulk query."""
    query = {
        "query": {"match_all": {}},
        "size": 10000,
    }

    try:
        data = await search("wazuh-states-vulnerabilities-*", query, username, password)
        hits = data.get("hits", {}).get("hits", [])
        
        result = {}
        for h in hits:
            source = h["_source"]
            agent_id = source.get("agent", {}).get("id")
            if not agent_id: continue
            
            if agent_id not in result:
                result[agent_id] = []
                
            result[agent_id].append({
                "cve": source.get("vulnerability", {}).get("id"),
                "name": source.get("package", {}).get("name"),
                "version": source.get("package", {}).get("version"),
                "severity": source.get("vulnerability", {}).get("severity", "Unknown"),
                "cvss": source.get("vulnerability", {}).get("score", {}).get("base"),
                "condition": source.get("vulnerability", {}).get("scanner", {}).get("condition"),
                "title": source.get("vulnerability", {}).get("title") or source.get("vulnerability", {}).get("id"),
            })
        return result
    except Exception as e:
        logger.warning("All active vulnerabilities fetch failed: %s", e)
        return {}


async def get_fim_history(agent_id: str, username: Optional[str] = None, password: Optional[str] = None) -> list:
    """Fetch File Integrity Monitoring history."""
    query = {
        "query": {
            "bool": {
                "must": [
                    {"term": {"agent.id": agent_id}},
                    {"term": {"rule.groups": "syscheck"}},
                ]
            }
        },
        "sort": [{"timestamp": {"order": "desc"}}],
        "size": 20,
    }

    try:
        data = await search("wazuh-alerts-*", query, username, password)
        return [
            {
                "file": h["_source"].get("syscheck", {}).get("path")
                or h["_source"].get("syscheck", {}).get("file"),
                "event": h["_source"].get("syscheck", {}).get("event"),
                "mtime": h["_source"].get("timestamp"),
            }
            for h in data.get("hits", {}).get("hits", [])
        ]
    except Exception:
        return []


async def get_sca_history(agent_id: str, username: Optional[str] = None, password: Optional[str] = None) -> list:
    """Fetch Security Configuration Assessment history."""
    query = {
        "query": {
            "bool": {
                "must": [
                    {"term": {"agent.id": agent_id}},
                    {"term": {"rule.groups": "sca"}},
                ]
            }
        },
        "sort": [{"timestamp": {"order": "desc"}}],
        "size": 20,
    }

    try:
        data = await search("wazuh-alerts-*", query, username, password)
        return [
            {
                "name": h["_source"].get("data", {}).get("sca", {}).get("policy"),
                "result": h["_source"].get("data", {}).get("sca", {}).get("result"),
                "end_scan": h["_source"].get("timestamp"),
            }
            for h in data.get("hits", {}).get("hits", [])
        ]
    except Exception:
        return []
