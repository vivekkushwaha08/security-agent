"""Live vulnerability intelligence lookups. No local vulnerability database is used."""
from __future__ import annotations
import os
from typing import Any
import httpx


def _headers(token_env: str | None = None) -> dict[str, str]:
    headers = {"Accept": "application/json", "User-Agent": "security-agent/0.1"}
    token = os.getenv(token_env, "") if token_env else ""
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


async def _get(client: httpx.AsyncClient, url: str, *, headers: dict[str, str] | None = None,
               params: dict[str, Any] | None = None) -> dict[str, Any]:
    response = await client.get(url, headers=headers, params=params)
    response.raise_for_status()
    return {"url": str(response.url), "status": response.status_code, "data": response.json()}


async def _post(client: httpx.AsyncClient, url: str, payload: dict[str, Any]) -> dict[str, Any]:
    response = await client.post(url, json=payload)
    response.raise_for_status()
    return {"url": str(response.url), "status": response.status_code, "data": response.json()}


async def lookup_osv(packages: list[dict[str, str]], timeout: float = 20) -> dict[str, Any]:
    """packages: [{name, version, ecosystem}], queried against OSV live API."""
    async with httpx.AsyncClient(timeout=timeout) as client:
        results = []
        for package in packages:
            query = {"version": package["version"], "package": {
                "name": package["name"], "ecosystem": package["ecosystem"]}}
            try:
                result = await _post(client, "https://api.osv.dev/v1/query", query)
                results.append({"package": package, **result})
            except httpx.HTTPError as exc:
                results.append({"package": package, "error": str(exc), "verified": False})
        return {"source": "OSV.dev", "checked_online": True, "results": results}


async def lookup_nvd(keyword: str, timeout: float = 20) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            result = await _get(client, "https://services.nvd.nist.gov/rest/json/cves/2.0",
                               headers=_headers("NVD_API_KEY"),
                               params={"keywordSearch": keyword, "resultsPerPage": 50})
            return {"source": "NVD", "checked_online": True, **result}
        except httpx.HTTPError as exc:
            return {"source": "NVD", "checked_online": True, "error": str(exc), "verified": False}


async def lookup_github_advisories(ecosystem: str, package_name: str,
                                   timeout: float = 20) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            result = await _get(client, "https://api.github.com/advisories",
                                headers=_headers("GITHUB_TOKEN"),
                                params={"ecosystem": ecosystem, "affects": package_name, "per_page": 100})
            return {"source": "GitHub Security Advisories", "checked_online": True, **result}
        except httpx.HTTPError as exc:
            return {"source": "GitHub Security Advisories", "checked_online": True,
                    "error": str(exc), "verified": False}


async def lookup_cisa_kev(timeout: float = 20) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            result = await _get(client, "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json")
            return {"source": "CISA KEV", "checked_online": True, **result}
        except httpx.HTTPError as exc:
            return {"source": "CISA KEV", "checked_online": True, "error": str(exc), "verified": False}


async def lookup_endoflife(product: str, timeout: float = 20) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            result = await _get(client, f"https://endoflife.date/api/{product}.json")
            return {"source": "endoflife.date", "checked_online": True, **result}
        except httpx.HTTPError as exc:
            return {"source": "endoflife.date", "checked_online": True, "error": str(exc), "verified": False}


async def investigate_online(packages: list[dict[str, str]], keywords: list[str],
                             eol_products: list[str] | None = None) -> dict[str, Any]:
    """Run live lookups. A failed source is reported as unverified, never silently clean."""
    results: dict[str, Any] = {"checked_online": True, "osv": [], "nvd": [],
                               "github_advisories": [], "cisa_kev": None, "endoflife": []}
    for package in packages:
        results["osv"].append(await lookup_osv([package]))
        results["github_advisories"].append(await lookup_github_advisories(
            package.get("ecosystem", ""), package["name"]))
    for keyword in keywords:
        results["nvd"].append(await lookup_nvd(keyword))
    results["cisa_kev"] = await lookup_cisa_kev()
    for product in eol_products or []:
        results["endoflife"].append(await lookup_endoflife(product))
    return results
