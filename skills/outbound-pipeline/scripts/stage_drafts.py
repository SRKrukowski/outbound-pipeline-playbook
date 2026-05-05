#!/usr/bin/env python3
"""Stage 5: create Gmail drafts via Composio (preferred) or raw Gmail API.

For each drafted email, push it into the user's Gmail Drafts folder. Never
sends. Returns a list of staged draft IDs for tracking.
"""
from __future__ import annotations

import base64
import json
import os
import urllib.request
import urllib.error
from email.mime.text import MIMEText


def build_raw_message(to_email: str, subject: str, body: str, sender: str) -> str:
    """Build a base64url-encoded RFC 2822 message for Gmail API."""
    msg = MIMEText(body, "plain", "utf-8")
    msg["to"] = to_email
    msg["from"] = sender
    msg["subject"] = subject
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8").rstrip("=")
    return raw


def stage_via_composio(drafts: list[dict], sender: str, composio_key: str) -> list[dict]:
    """Use Composio's Gmail action to create drafts."""
    staged = []
    for d in drafts:
        to_email = d.get("contact_email") or ""
        if not to_email:
            print(f"      [skip] no email for {d.get('company_name','?')}")
            continue
        payload = {
            "action": "GMAIL_CREATE_EMAIL_DRAFT",
            "params": {
                "recipient_email": to_email,
                "subject": d.get("draft_subject", ""),
                "body": d.get("draft_body", ""),
                "is_html": False,
            },
        }
        req = urllib.request.Request(
            "https://backend.composio.dev/api/v2/actions/execute",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "x-api-key": composio_key,
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="ignore")
            print(f"      [warn] Composio {e.code} for {to_email}: {body[:200]}; skipping")
            continue
        except urllib.error.URLError as e:
            print(f"      [warn] Composio network error for {to_email}: {e.reason}; skipping")
            continue

        draft_id = data.get("data", {}).get("id") or data.get("id") or "unknown"
        staged.append({**d, "gmail_draft_id": draft_id})
    return staged


def stage_via_raw_gmail(drafts: list[dict], sender: str) -> list[dict]:
    """Use Google Gmail API directly with refresh-token OAuth flow."""
    refresh_token = os.environ.get("GOOGLE_REFRESH_TOKEN", "")
    client_id = os.environ.get("GOOGLE_CLIENT_ID", "")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET", "")
    if not all([refresh_token, client_id, client_secret]):
        raise SystemExit("Raw Gmail mode requires GOOGLE_REFRESH_TOKEN, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET. Set them in .env or use Composio.")

    token_payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }
    token_req = urllib.request.Request(
        "https://oauth2.googleapis.com/token",
        data=json.dumps(token_payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(token_req, timeout=30) as resp:
        access_token = json.loads(resp.read().decode("utf-8"))["access_token"]

    staged = []
    for d in drafts:
        to_email = d.get("contact_email") or ""
        if not to_email:
            continue
        raw = build_raw_message(to_email, d.get("draft_subject", ""), d.get("draft_body", ""), sender)
        payload = {"message": {"raw": raw}}
        req = urllib.request.Request(
            "https://gmail.googleapis.com/gmail/v1/users/me/drafts",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            staged.append({**d, "gmail_draft_id": data.get("id", "unknown")})
        except urllib.error.HTTPError as e:
            print(f"      [warn] Gmail {e.code} for {to_email}; skipping")
            continue
    return staged


def stage_drafts(drafts: list[dict], sender: str, composio_key: str) -> list[dict]:
    if composio_key:
        return stage_via_composio(drafts, sender, composio_key)
    return stage_via_raw_gmail(drafts, sender)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    args = parser.parse_args()
    drafts = [json.loads(line) for line in open(args.input, encoding="utf-8")]
    out = stage_drafts(drafts, os.environ.get("SENDER_EMAIL", ""), os.environ.get("COMPOSIO_API_KEY", ""))
    print(json.dumps(out, indent=2))
