# Outbound Pipeline

> One ICP definition in, personalized research-backed cold-email drafts out, waiting in your Gmail. One command in Claude Code. Nothing sends until a human clicks Send.

![License](https://img.shields.io/badge/license-MIT-blue) ![Claude Code](https://img.shields.io/badge/Claude%20Code-skill-8A2BE2) ![Python](https://img.shields.io/badge/python-3.10%2B-green)

```
ICP spec  ->  Exa research  ->  Apollo enrichment  ->  Claude drafting  ->  Gmail drafts
```

Cold outreach is usually one of two bad options: write it by hand (a full day for ten good emails) or pay an agency $3-5K/month for output that still reads like a mail merge. This pipeline does the research, enrichment, and personalization from a single command, and every email lands in Gmail Drafts for you to review and send. No auto-sending, ever.

## Example output

A draft generated from an ICP targeting heads of operations at mid-size manufacturers showing recent hiring activity (illustrative):

```
Subject: the 3rd ops hire this quarter

Hi Dana,

Saw Lakeside Components has posted three operations roles since
March, including the new continuous-improvement lead. Usually
when a plant scales the ops team that fast, the reporting layer
is the first thing that quietly breaks.

We help manufacturers stand that layer up before it becomes the
bottleneck. Worth a 15-minute call next week to compare notes?

Scott
```

The research signal (the hiring activity) is pulled live by Exa, the contact is verified by Apollo, and the copy is written by Claude against your value proposition. No two drafts are templated.

## Quickstart

```bash
git clone https://github.com/SRKrukowski/outbound-pipeline-playbook.git
cd outbound-pipeline-playbook
claude
```

Then, inside Claude Code:

```
Read playbook.md and walk me through the setup.
```

Claude checks prerequisites, collects any missing API keys, installs the skill into `~/.claude/skills/outbound-pipeline/`, drops an ICP template into your working directory, and runs a free dry-run before any paid call happens.

## What you need

| Service | Why | Cost |
|---|---|---|
| Anthropic API | Claude writes the drafts | ~$5-15/mo at typical volume |
| Exa API | live prospect research signals | free tier ~10 searches/day; paid from $10/mo |
| Apollo.io | verified email + title enrichment | free tier 50 credits/mo; paid from $59/mo |
| Google Workspace + Gmail API | draft staging | free |
| Composio (optional) | handles Gmail + Apollo OAuth for you | free tier covers personal use |

The walkthrough pauses and tells you exactly what to provision if anything is missing.

## How it works

```
1. Parse     read your ICP spec, normalize to a query plan
2. Discover  Exa surfaces prospects matching your intent signal
3. Enrich    Apollo adds verified email + decision-maker title
4. Draft     Claude writes each email against your value prop
5. Stage     drafts land in Gmail, never sent automatically
```

Full design rationale for each stage lives in [`playbook.md`](./playbook.md).

## Safety

- Never auto-sends. Drafts only. You review and click Send.
- Defaults to a free dry-run; the first paid run is opt-in.
- Stops and names the missing key rather than inventing a fallback.

## License

MIT. Use it, fork it, build on it.

## Author

Built by [Scott Krukowski](https://www.scottkrukowski.com). Design notes and the full write-up are at [The Wise Operator](https://thewiseoperator.com).
