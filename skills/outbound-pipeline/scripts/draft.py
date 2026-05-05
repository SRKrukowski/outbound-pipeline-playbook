#!/usr/bin/env python3
"""Stage 4: Claude drafts a personalized email per enriched prospect.

Each draft references a specific Exa research signal and ties it to the ICP
value proposition. Output is a structured JSON object the Gmail stager consumes.
"""
from __future__ import annotations

import json
import os
import urllib.request
import urllib.error


SYSTEM_PROMPT = """You write cold outbound emails for a non-technical operator who values honesty over volume. Your job is to produce one personalized email per prospect using the research signal and contact information provided.

Hard rules:
- The opening sentence must reference the specific research signal. Not a generic compliment.
- The body explains the value proposition in plain language, no jargon.
- The CTA at the end is exactly the one the user specified.
- Sign-off is the sender name only. No marketing footer.
- Length: 90 to 130 words including signature. No exceptions.
- Tone: peer to peer. Not a vendor pitch. Not a desperate ask.
- No em dashes. Use commas, colons, or periods.
- No "I hope this finds you well" or similar templated openers.
- No "circling back," "touching base," "synergy," or other sales-speak.
- If the research signal is weak or missing, say so honestly inside the email rather than fabricating a connection.

Output format: a JSON object with keys subject, body. Nothing else.
"""


def draft_one(prospect: dict, icp: dict, sender: dict, api_key: str) -> dict:
    user_prompt = f"""ICP context:
- Target role: {icp.get('target role','')}
- Value proposition: {icp.get('value proposition','')}
- Call to action: {icp.get('call to action','')}
- Tone: {icp.get('tone','consultative')}

Sender:
- Name: {sender.get('name','')}
- Title: {sender.get('title','')}
- Company: {sender.get('company','')}
- Credibility anchor: {icp.get('sender context','')}

Prospect:
- Contact name: {prospect.get('contact_name','')}
- Contact title: {prospect.get('contact_title','')}
- Company: {prospect.get('company_name','')}
- Research signal (from Exa): {prospect.get('research_signal','')}

Write one email. Return JSON: {{"subject": "...", "body": "..."}}.
"""
    payload = {
        "model": "claude-sonnet-4-6",
        "max_tokens": 600,
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": user_prompt}],
    }
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        raise SystemExit(f"Anthropic API failed: {e.code} {body}")
    except urllib.error.URLError as e:
        raise SystemExit(f"Anthropic API network error: {e.reason}")

    text = "".join(part.get("text", "") for part in data.get("content", []) if part.get("type") == "text")
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:].strip()
        text = text.strip("`").strip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        parsed = {"subject": "(parse error)", "body": text}

    return {
        **prospect,
        "draft_subject": parsed.get("subject", ""),
        "draft_body": parsed.get("body", ""),
    }


def draft_emails(enriched: list[dict], icp: dict, api_key: str) -> list[dict]:
    sender = {
        "name": os.environ.get("SENDER_NAME", ""),
        "title": os.environ.get("SENDER_TITLE", ""),
        "company": os.environ.get("SENDER_COMPANY", ""),
        "email": os.environ.get("SENDER_EMAIL", ""),
    }
    out = []
    for p in enriched:
        out.append(draft_one(p, icp, sender, api_key))
    return out


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--icp", required=True)
    args = parser.parse_args()
    enriched = [json.loads(line) for line in open(args.input, encoding="utf-8")]
    icp = {"target role": "VP Engineering", "value proposition": "test", "call to action": "15-min call"}
    out = draft_emails(enriched, icp, os.environ["ANTHROPIC_API_KEY"])
    print(json.dumps(out, indent=2))
