#!/usr/bin/env python3
"""Stage 2: Exa-powered candidate discovery.

Builds a query from the ICP intent signal + verticals + geography, calls Exa's
search-and-contents endpoint, returns a list of candidate companies with the
research signal that justifies including them.
"""
from __future__ import annotations

import json
import urllib.request
import urllib.error


def build_query(icp: dict) -> str:
    """Compose a natural-language Exa query from ICP fields."""
    parts = []
    if "intent signal" in icp:
        parts.append(icp["intent signal"])
    if "verticals" in icp:
        parts.append(f"in {icp['verticals']}")
    if "geography" in icp:
        parts.append(f"based in {icp['geography']}")
    if "company size" in icp:
        parts.append(f"({icp['company size']})")
    return ". ".join(parts).strip()


def search_candidates(icp: dict, limit: int, api_key: str) -> list[dict]:
    """Run an Exa search and return enriched candidate records."""
    query = build_query(icp)
    payload = {
        "query": query,
        "type": "auto",
        "numResults": limit,
        "contents": {
            "text": {"maxCharacters": 1500},
            "highlights": {"numSentences": 3, "highlightsPerUrl": 2},
        },
        "useAutoprompt": True,
    }
    req = urllib.request.Request(
        "https://api.exa.ai/search",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise SystemExit(f"Exa search failed: {e.code} {e.read().decode('utf-8', errors='ignore')}")
    except urllib.error.URLError as e:
        raise SystemExit(f"Exa search network error: {e.reason}")

    results = data.get("results", [])
    candidates = []
    for r in results:
        signal = r.get("highlights") or [r.get("text", "")[:300]]
        signal_text = " ".join(signal).strip() if isinstance(signal, list) else str(signal)
        candidates.append({
            "company_name": r.get("title", "").split("|")[0].strip() or r.get("url", ""),
            "url": r.get("url", ""),
            "research_signal": signal_text[:600],
            "published_date": r.get("publishedDate", ""),
            "source_score": r.get("score", 0),
        })
    return candidates


if __name__ == "__main__":
    import argparse
    import os
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", required=True)
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()
    out = search_candidates({"intent signal": args.query}, args.limit, os.environ["EXA_API_KEY"])
    print(json.dumps(out, indent=2))
