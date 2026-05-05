#!/usr/bin/env python3
"""Stage 3: Apollo.io contact enrichment.

For each candidate company, query Apollo's people-search endpoint to find a
verified email + decision-maker title matching the ICP target role.
"""
from __future__ import annotations

import json
import urllib.request
import urllib.error
from urllib.parse import urlparse


APOLLO_PEOPLE_SEARCH = "https://api.apollo.io/api/v1/mixed_people/search"


def domain_from_url(url: str) -> str:
    if not url:
        return ""
    parsed = urlparse(url)
    host = parsed.netloc or url
    if host.startswith("www."):
        host = host[4:]
    return host.split("/")[0]


def enrich_candidates(candidates: list[dict], api_key: str) -> list[dict]:
    """Query Apollo per candidate, attach contact fields. Drops candidates with no match."""
    enriched = []
    for c in candidates:
        domain = domain_from_url(c.get("url", ""))
        if not domain:
            continue
        payload = {
            "q_organization_domains_list": [domain],
            "page": 1,
            "per_page": 5,
            "person_titles": ["VP", "Director", "Head", "Owner", "Founder", "President", "Chief"],
        }
        req = urllib.request.Request(
            APOLLO_PEOPLE_SEARCH,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Cache-Control": "no-cache",
                "X-Api-Key": api_key,
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 429:
                print(f"      [warn] Apollo 429 rate limit on {domain}; skipping")
                continue
            print(f"      [warn] Apollo {e.code} for {domain}; skipping")
            continue
        except urllib.error.URLError as e:
            print(f"      [warn] Apollo network error for {domain}: {e.reason}; skipping")
            continue

        people = data.get("people") or data.get("contacts") or []
        if not people:
            continue
        person = people[0]
        enriched.append({
            **c,
            "contact_name": (person.get("name") or
                             f"{person.get('first_name','')} {person.get('last_name','')}").strip(),
            "contact_first_name": person.get("first_name", ""),
            "contact_email": person.get("email") or "",
            "contact_title": person.get("title", ""),
            "company_size_estimate": person.get("organization", {}).get("estimated_num_employees", ""),
            "linkedin_url": person.get("linkedin_url", ""),
        })
    return enriched


if __name__ == "__main__":
    import argparse
    import os
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    args = parser.parse_args()
    candidates = [json.loads(line) for line in open(args.input, encoding="utf-8")]
    out = enrich_candidates(candidates, os.environ["APOLLO_API_KEY"])
    print(json.dumps(out, indent=2))
