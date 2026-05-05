# Outbound Pipeline Playbook

A Claude Code skill + install playbook for the AI-assisted outbound workflow described on [The Wise Operator](https://thewiseoperator.com/workflows/outbound-pipeline/). One command kicks off a five-stage pipeline that turns an ICP definition into Gmail drafts, every email reviewed by a human before sending.

```
ICP spec  ->  Exa research  ->  Apollo enrichment  ->  Claude drafting  ->  Gmail drafts
```

## What's in this repo

```
.
├── playbook.md                          # Read this in Claude Code to install everything
├── skills/
│   └── outbound-pipeline/
│       ├── SKILL.md                     # The runtime skill that executes the pipeline
│       └── scripts/
│           ├── run_pipeline.py          # Orchestrator (call this one)
│           ├── exa_search.py            # Stage 2: discovery
│           ├── enrich.py                # Stage 3: enrichment
│           ├── draft.py                 # Stage 4: drafting
│           └── stage_drafts.py          # Stage 5: Gmail drafts
├── templates/
│   └── icp-spec.template.md             # Copy this and fill in your ICP
├── .env.example                         # Which keys to provision
└── LICENSE                              # MIT
```

## Install in 60 seconds

```bash
git clone https://github.com/SRKrukowski/outbound-pipeline-playbook.git
cd outbound-pipeline-playbook
claude
```

Then in Claude Code, type:

```
Read playbook.md and walk me through the setup.
```

Claude will check prerequisites, ask for missing API keys, install the skill into `~/.claude/skills/outbound-pipeline/`, copy the ICP template into your working directory, and run a dry-run before any real API charges.

## Prerequisites (you cannot skip these)

- **Anthropic API key** — Claude does the drafting. ~$5-15/mo at typical volume.
- **Exa API key** — research signals. Free tier covers ~10 searches/day; paid starts at $10/mo.
- **Apollo.io account** — contact enrichment. Free tier gives 50 credits/mo; paid plans start at $59/mo.
- **Google Workspace + Gmail API enabled** — drafts staging. Free.
- **Composio account (optional but recommended)** — handles the OAuth dance for Gmail and Apollo so you don't have to wire raw API clients. Free tier covers personal use.

If any of these are missing, the playbook walkthrough will pause and tell you which one to set up before continuing.

## Why this exists

Cold outbound done well needs fresh research, real enrichment, and personalization that doesn't read like a template. Doing it by hand for ten prospects is a full day. Hiring an agency burns $3-5K/month and still produces templated output. This pipeline replaces that with a single command, but every email enters Gmail as a draft. Nothing sends until a human reads it and clicks Send.

## License

MIT. Use it, fork it, build on it. Attribution to The Wise Operator appreciated but not required.

## Author

Built by [Scott Krukowski](https://www.scottkrukowski.com), editor of [The Wise Operator](https://thewiseoperator.com). Questions or improvements: scott@thewiseoperator.com.
