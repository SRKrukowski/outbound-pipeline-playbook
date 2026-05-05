# Outbound Pipeline Playbook — Install Walkthrough

You are reading this file because a human has opened it in Claude Code and asked you to walk them through setup. Treat this as your runbook. Follow it step by step. Do not skip phases. Pause and ask the user every time you need a credential or a decision.

The goal: install the `outbound-pipeline` skill into the user's Claude Code environment, get every required API key in place, copy the ICP template into the user's working directory, and run a free dry-run before any paid API calls happen.

When the user types something like "Read playbook.md and walk me through it," begin from Phase 1.

---

## Phase 1: Greeting + scope

Greet the user briefly. Tell them what they are about to install (the outbound pipeline) and what they will have when it is done (a `/outbound-pipeline` command in Claude Code that takes their ICP definition and produces Gmail drafts). Confirm they want to proceed.

Then tell them honestly:

- This will take 10 to 25 minutes depending on which API accounts they already have.
- They will need to provision keys from Anthropic, Exa, Apollo, and either Composio or raw Gmail OAuth.
- Some of those services have free tiers; some require billing. The walkthrough will flag costs at each step.
- Nothing will charge their card during this walkthrough. The first paid step is opt-in at the very end (a real run against ten prospects).

Wait for confirmation.

---

## Phase 2: Prerequisite check

Ask the user one question at a time. Do not batch them. For each prerequisite, if they have it, take the value and store it in their `.env` file. If they do not have it, give them the exact link and exact steps to provision it, then wait.

### 2a. Claude Code

Confirm they are in Claude Code (which they are, since they are reading this). Confirm `~/.claude/skills/` exists. Create it if not.

### 2b. Anthropic API key

Ask: "Do you already have an Anthropic API key?"

If yes, ask them to paste it. Save to `.env` as `ANTHROPIC_API_KEY`.

If no:

> Go to https://console.anthropic.com/settings/keys and click Create Key. Give it a name like `outbound-pipeline`. Set a monthly spend limit of $20 to start (you can raise it later). Paste the key back here when you have it.

### 2c. Exa API key

Ask: "Do you have an Exa API key? Exa is the research search engine that finds prospect signals — recent news, product launches, hiring announcements."

If yes, paste. Save as `EXA_API_KEY`.

If no:

> Sign up at https://exa.ai (free tier covers ~10 searches per day, which is enough to test). After verifying email, go to https://dashboard.exa.ai/api-keys and create a key. Paste it back here.

### 2d. Apollo.io API key

Ask: "Do you have an Apollo.io account? Apollo turns a company name into a verified email address and decision-maker title."

If yes, paste. Save as `APOLLO_API_KEY`.

If no:

> Sign up at https://www.apollo.io (free plan gives 50 enrichment credits per month, enough for the dry-run). Go to https://app.apollo.io/#/settings/integrations/api and copy your API key. Paste it back here.

Tell the user: "If you only have free credits and you run more than 50 prospects in a month, enrichment will fail silently for the overflow. The skill will warn you when you cross 40."

### 2e. Composio (recommended) OR raw Gmail OAuth

Ask: "Do you want to use Composio to handle Gmail + Apollo OAuth, or do you want to wire raw Gmail API yourself? Composio is easier; raw Gmail is more control."

If they pick Composio:

> Sign up at https://app.composio.dev (free tier covers personal use). Get your API key at https://app.composio.dev/api-keys. Paste it back. Then connect Gmail by visiting https://app.composio.dev/apps/gmail and clicking Connect. Tell me when that is done.

Save as `COMPOSIO_API_KEY`. Verify the Gmail connection by listing tools available to the key (`composio integrations list`).

If they pick raw Gmail OAuth:

> Go to https://console.cloud.google.com/apis/credentials. Create an OAuth 2.0 client (Desktop app). Download the credentials JSON. We need three values: GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, and a refresh token. I will walk you through generating the refresh token using a one-shot script.

For the refresh token, run `python skills/outbound-pipeline/scripts/auth_gmail.py` from the playbook directory and follow the browser flow. Save the printed `GOOGLE_REFRESH_TOKEN` to `.env`.

### 2f. Sender identity

Ask the user for `SENDER_NAME`, `SENDER_EMAIL`, `SENDER_TITLE`, `SENDER_COMPANY`. Save all four to `.env`.

---

## Phase 3: Install the skill

Copy `skills/outbound-pipeline/` (the entire directory, including SKILL.md and the `scripts/` folder) into `~/.claude/skills/outbound-pipeline/`.

Use this exact command:

```bash
cp -r skills/outbound-pipeline ~/.claude/skills/
```

On Windows PowerShell:

```powershell
Copy-Item -Recurse skills\outbound-pipeline $HOME\.claude\skills\
```

Verify the copy by listing `~/.claude/skills/outbound-pipeline/`. Confirm `SKILL.md` and `scripts/` are both present.

Tell the user: "The skill is installed. From any Claude Code session in any directory, you can now type `/outbound-pipeline` and it will activate."

---

## Phase 4: Copy the ICP template

Copy `templates/icp-spec.template.md` into the user's current working directory as `icp-spec.md`. Then walk them through filling it in. Ask them, in order:

1. What role are you targeting? (e.g., VP of Engineering, Head of Operations, Owner)
2. What company size? (employee count range)
3. What geography? (US, EMEA, specific states/countries)
4. What verticals? (e.g., SaaS, manufacturing, healthcare)
5. What intent signal are you looking for? (e.g., recent funding, hiring spree, product launch, ESOP transition)
6. What is your one-sentence value proposition for this audience?
7. What is the call to action you want at the end of every email? (e.g., "15-minute call next week," "send a one-page brief")

Write each answer into `icp-spec.md` as you go. Show the user the final filled-in spec and confirm it looks right before moving on.

---

## Phase 5: Dry run (free, no API charges)

Run the pipeline in dry-run mode. This:

- Hits Exa (free tier, no charge)
- **Skips** Apollo enrichment (synthetic test data instead)
- Calls Claude (~$0.10 of API spend total)
- **Skips** Gmail draft staging (writes drafts to `out/drafts.jsonl` instead)

Run:

```bash
python ~/.claude/skills/outbound-pipeline/scripts/run_pipeline.py \
  --icp icp-spec.md \
  --limit 3 \
  --dry-run
```

When it finishes, read the first draft from `out/drafts.jsonl` aloud to the user. Confirm:

- The research signal is real (not made up)
- The draft references the prospect by name
- The draft does not feel templated
- The CTA matches what they specified in the ICP

If anything looks off, tell the user which step failed and offer to retune. Common issues:

- Empty Exa results -> the ICP intent signal is too narrow. Loosen it.
- Generic draft copy -> the ICP value proposition is too vague. Sharpen it.
- Wrong tone -> we can tune the system prompt in `skills/outbound-pipeline/scripts/draft.py`.

---

## Phase 6: First real run (paid, opt-in)

Tell the user: "We are about to run the pipeline against five real prospects with full enrichment and Gmail draft staging. Estimated cost: $0.50 in API spend, 5 Apollo credits used. Continue?"

If yes, run:

```bash
python ~/.claude/skills/outbound-pipeline/scripts/run_pipeline.py \
  --icp icp-spec.md \
  --limit 5
```

When it finishes, the user will have five drafts sitting in their Gmail Drafts folder. Tell them: "Open Gmail. Review each draft. Edit anything that needs editing. Click Send when you are ready. Nothing has gone out yet."

---

## Phase 7: Operate

Tell the user how to run this regularly:

> From now on, in any Claude Code session, type `/outbound-pipeline` and the skill will pick up your `icp-spec.md` and run the pipeline. To target a different audience, edit `icp-spec.md` or create a new one and pass `--icp <filename>`.
>
> The skill always defaults to dry-run mode unless you confirm a paid run. You can change this in `.env` by setting `DRY_RUN=false` permanently (not recommended).

End the walkthrough by suggesting they read the full editorial article at https://thewiseoperator.com/workflows/outbound-pipeline/ for the design decisions behind each step, and the upcoming RevOps companion article that connects this output to a CRM.

---

## Failure modes (consult these if a phase fails)

- **Exa returns 401** -> key is wrong or revoked. Re-paste from https://dashboard.exa.ai/api-keys.
- **Apollo returns 429** -> monthly credits exhausted. Either wait until next month or upgrade plan.
- **Gmail draft creation fails** -> Composio token expired or Gmail OAuth scope missing. Reconnect at https://app.composio.dev/apps/gmail.
- **Anthropic returns 429** -> spend limit hit. Raise the limit or wait until reset.
- **`out/drafts.jsonl` is empty** -> no prospects passed the Exa filter. Loosen the ICP intent signal.
