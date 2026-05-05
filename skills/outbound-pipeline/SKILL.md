---
name: outbound-pipeline
description: Run the five-stage outbound pipeline (ICP -> Exa research -> Apollo enrichment -> Claude drafting -> Gmail drafts). Invoke when the user wants to generate personalized cold outreach drafts from an ICP definition file.
---

# Outbound Pipeline

When activated, this skill runs the user's outbound pipeline end to end and reports back with a count of drafts staged plus any failures.

## When to invoke

- User says "run the outbound pipeline" or "run /outbound-pipeline"
- User says "generate outbound drafts from my ICP"
- User points at an ICP file and says "draft emails for these prospects"

## Inputs

- **icp-spec.md** in the user's working directory (default), OR a path passed as `--icp <path>`
- **Limit** of how many prospects to process this run (default: 10, capped at 50)
- **Dry-run flag** (default: read from `DRY_RUN` env var; falsy means live)

## How to run

Use the orchestrator script:

```bash
python ~/.claude/skills/outbound-pipeline/scripts/run_pipeline.py \
  --icp <path-to-icp-file> \
  --limit <N> \
  [--dry-run]
```

The orchestrator chains the five stages:

1. **Parse** — read ICP spec, normalize to a query plan
2. **Discover** — `exa_search.py` calls Exa with the query plan, writes `out/candidates.jsonl`
3. **Enrich** — `enrich.py` adds verified email + title via Apollo, writes `out/enriched.jsonl` (skipped in dry-run)
4. **Draft** — `draft.py` calls Claude with the research + enriched contact + ICP value prop, writes `out/drafts.jsonl`
5. **Stage** — `stage_drafts.py` creates Gmail drafts via Composio (or raw Gmail API), writes `out/staged.jsonl` (skipped in dry-run)

## After running

Report back to the user with:

- How many candidates Exa surfaced
- How many made it through enrichment (or note dry-run skip)
- How many drafts Claude generated
- How many landed in Gmail Drafts (or note dry-run skip + path to `out/drafts.jsonl`)
- Any failures with the specific stage and error message

If the user asks to see a specific draft, read the JSONL and pretty-print the requested entry.

## Common adjustments

- "Make the draft shorter" -> tune system prompt in `scripts/draft.py`
- "Target a different audience" -> edit `icp-spec.md` or pass a different `--icp`
- "Run more prospects" -> raise `--limit`, watch Apollo credit usage
- "Stop using Apollo" -> set `DRY_RUN=true` in `.env` for synthetic enrichment, or remove `enrich.py` from the orchestrator chain in `run_pipeline.py`

## Hard rules

- Never auto-send emails. Always create drafts and let the human review.
- Never write to the user's Sent folder. Only Drafts.
- If the ICP file is missing, ask the user to run the playbook walkthrough first.
- If any required env var is missing, report which one and stop. Do not invent fallbacks.
