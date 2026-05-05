#!/usr/bin/env python3
"""Outbound pipeline orchestrator.

Chains: ICP parse -> Exa search -> Apollo enrichment -> Claude drafting -> Gmail draft staging.

In dry-run mode, skips Apollo enrichment (synthesizes test data) and skips Gmail
draft staging (writes drafts to out/drafts.jsonl only).

Usage:
    python run_pipeline.py --icp icp-spec.md --limit 5 [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

from exa_search import search_candidates
from enrich import enrich_candidates
from draft import draft_emails
from stage_drafts import stage_drafts

ROOT = Path(__file__).resolve().parent
OUT = Path("out")


def load_env() -> dict:
    """Load .env from CWD or parent directories. Returns missing required keys."""
    env_path = None
    for d in [Path.cwd(), Path.cwd().parent, ROOT.parent.parent.parent]:
        candidate = d / ".env"
        if candidate.exists():
            env_path = candidate
            break

    if env_path:
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

    return {
        "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY", ""),
        "EXA_API_KEY": os.environ.get("EXA_API_KEY", ""),
        "APOLLO_API_KEY": os.environ.get("APOLLO_API_KEY", ""),
        "COMPOSIO_API_KEY": os.environ.get("COMPOSIO_API_KEY", ""),
        "SENDER_NAME": os.environ.get("SENDER_NAME", ""),
        "SENDER_EMAIL": os.environ.get("SENDER_EMAIL", ""),
    }


def parse_icp(path: Path) -> dict:
    """Extract structured fields from a filled-in ICP markdown file."""
    text = path.read_text(encoding="utf-8")
    fields = {}
    sections = re.split(r"\n## ", "\n" + text)
    for section in sections[1:]:
        lines = section.split("\n", 1)
        heading = lines[0].strip().lower()
        body = lines[1] if len(lines) > 1 else ""
        match = re.search(r"```\s*\n(.*?)\n```", body, re.DOTALL)
        if not match:
            continue
        value = match.group(1).strip()
        if value and value != "[fill in]" and value != "[fill in or leave blank]":
            fields[heading] = value
    required = ["target role", "intent signal", "value proposition", "call to action"]
    missing = [r for r in required if r not in fields]
    if missing:
        sys.exit(f"ICP spec is missing required fields: {', '.join(missing)}. Edit {path} and fill them in.")
    return fields


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--icp", default="icp-spec.md", help="Path to ICP spec markdown")
    parser.add_argument("--limit", type=int, default=10, help="Max prospects to process (cap 50)")
    parser.add_argument("--dry-run", action="store_true", help="Skip Apollo + Gmail; write drafts to out/")
    args = parser.parse_args()

    args.limit = min(args.limit, 50)
    dry_run = args.dry_run or os.environ.get("DRY_RUN", "false").lower() == "true"

    env = load_env()
    icp_path = Path(args.icp)
    if not icp_path.exists():
        sys.exit(f"ICP file not found at {icp_path}. Run the playbook walkthrough first.")

    print(f"== Outbound pipeline ==")
    print(f"ICP:       {icp_path}")
    print(f"Limit:     {args.limit}")
    print(f"Dry run:   {dry_run}\n")

    icp = parse_icp(icp_path)

    print("[1/5] Parsed ICP spec")
    for k, v in icp.items():
        snippet = v.replace("\n", " ")[:80]
        print(f"      {k}: {snippet}")
    print()

    print("[2/5] Discovering candidates via Exa...")
    if not env["EXA_API_KEY"]:
        sys.exit("EXA_API_KEY missing. Set it in .env.")
    candidates = search_candidates(icp, limit=args.limit, api_key=env["EXA_API_KEY"])
    write_jsonl(OUT / "candidates.jsonl", candidates)
    print(f"      {len(candidates)} candidates -> out/candidates.jsonl\n")

    print("[3/5] Enriching contacts...")
    if dry_run:
        enriched = [{**c, "contact_name": "[Test First] [Test Last]", "contact_email": "test@example.com",
                     "contact_title": icp["target role"], "company_size_estimate": "synthetic"} for c in candidates]
        print(f"      {len(enriched)} enriched (synthetic, dry-run)\n")
    else:
        if not env["APOLLO_API_KEY"]:
            sys.exit("APOLLO_API_KEY missing. Set it in .env or use --dry-run.")
        enriched = enrich_candidates(candidates, api_key=env["APOLLO_API_KEY"])
        print(f"      {len(enriched)} enriched (Apollo)\n")
    write_jsonl(OUT / "enriched.jsonl", enriched)

    print("[4/5] Drafting emails with Claude...")
    if not env["ANTHROPIC_API_KEY"]:
        sys.exit("ANTHROPIC_API_KEY missing. Set it in .env.")
    drafts = draft_emails(enriched, icp=icp, api_key=env["ANTHROPIC_API_KEY"])
    write_jsonl(OUT / "drafts.jsonl", drafts)
    print(f"      {len(drafts)} drafts -> out/drafts.jsonl\n")

    print("[5/5] Staging Gmail drafts...")
    if dry_run:
        print(f"      Skipped (dry-run). Review out/drafts.jsonl manually.\n")
    else:
        composio_key = env["COMPOSIO_API_KEY"]
        sender = env["SENDER_EMAIL"] or os.environ.get("SENDER_EMAIL", "")
        staged = stage_drafts(drafts, sender=sender, composio_key=composio_key)
        write_jsonl(OUT / "staged.jsonl", staged)
        print(f"      {len(staged)} drafts staged in Gmail\n")

    print("== Done ==")
    print(f"Open Gmail Drafts to review. Nothing has sent.")


if __name__ == "__main__":
    main()
