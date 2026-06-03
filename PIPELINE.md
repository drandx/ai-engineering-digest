# AI Engineering Digest — Pipeline

Daily newsletter for AI & Software Engineers. Curated by Pepe, published to GitHub Pages.

**Live site:** https://drandx.github.io/ai-engineering-digest/

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  OpenClaw Cron (7:00 AM ET daily)                               │
│  Triggers isolated agent session: "newsletter-orchestrator"     │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│  Phase 1: RESEARCH (parallel sub-agents)                        │
│                                                                 │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐     │
│  │ Agent 1      │ │ Agent 2      │ │ Agent 3              │     │
│  │ AI/ML Tools  │ │ DevTools &   │ │ Community &          │     │
│  │ & Models     │ │ Frameworks   │ │ Trending             │     │
│  └──────┬───────┘ └──────┬───────┘ └──────────┬───────────┘     │
│         │                │                     │                │
│         └────────────────┼─────────────────────┘                │
│                          ▼                                      │
│  Phase 2: CURATE                                                │
│  Orchestrator deduplicates, validates traction, scores,         │
│  and structures articles into sections                          │
│                          │                                      │
│                          ▼                                      │
│  Phase 3: BUILD                                                 │
│  Generate JSON → Run newsletter_generate.py → HTML              │
│                          │                                      │
│                          ▼                                      │
│  Phase 4: PUBLISH                                               │
│  git add → commit → push → GitHub Pages auto-deploys            │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### 1. OpenClaw Cron Job

- **Name:** `ai-engineering-digest`
- **Schedule:** Daily at 7:00 AM ET
- **Target:** Isolated agent session (own context, won't block main session)
- **Model:** `claude-sonnet-4-6`

The cron triggers a self-contained agent session that runs the full pipeline.

### 2. Research Agents (3 parallel sub-agents)

Each agent searches the web independently and returns structured JSON:

| Agent | Domain | Search Queries |
|-------|--------|----------------|
| **AI/ML** | Models, coding agents, LLM tools | AI frameworks, model releases, coding agents |
| **DevTools** | Developer tools, OSS, infrastructure | New tools, GitHub trending, spec-driven dev |
| **Community** | HN, Reddit, X/Twitter discussions | What developers are excited about right now |

Each agent returns articles with: title, url, tldr, why_it_matters, traction level, evidence, use cases, tags, and source links.

### 3. Curation (orchestrator)

The orchestrator (the cron-triggered session) collects all research results and:
- Deduplicates across agents (same story found by multiple agents = higher signal)
- Validates traction claims
- Organizes into 3 sections: "AI Tools & Models", "Developer Tools & Frameworks", "Infrastructure & Production"
- Picks 5-6 highlights for the summary
- Checks previous issues to avoid repeating stories

### 4. HTML Generator (`scripts/newsletter_generate.py`)

Takes the curated JSON and produces:
- `issues/YYYY-MM-DD.html` — the daily issue
- `index.html` — redirects to latest + shows archive

### 5. GitHub Pages

Push triggers auto-deploy to https://drandx.github.io/ai-engineering-digest/

## File Structure

```
ai-engineering-digest/
├── PIPELINE.md              ← You are here
├── style.css                ← Newsletter styling (dark theme)
├── index.html               ← Auto-generated: redirects to latest issue
├── scripts/
│   └── newsletter_generate.py  ← JSON → HTML converter
└── issues/
    ├── 2026-06-03.json      ← Raw curated data
    └── 2026-06-03.html      ← Generated newsletter
```

## Quality Criteria

An article makes the cut if it meets ALL of these:

1. **Traction** — Evidence of real adoption (GitHub stars, enterprise users, community buzz, multiple independent mentions)
2. **Practical** — Useful for a Software Engineer / AI Engineer building products RIGHT NOW
3. **Use cases** — Has concrete, specific use cases (not just "this is cool")
4. **Not hype** — Skip announcements without adoption evidence

Traction levels:
- **High** — Proven, widely adopted, enterprise usage
- **Medium** — Growing, validated by early adopters
- **Emerging** — Early but with real evidence (not just a launch post)

## Manual Run

To trigger the newsletter manually outside the cron schedule:

```bash
# From OpenClaw, tell Pepe:
# "Run the newsletter pipeline for today"

# Or trigger the cron job directly:
# Use OpenClaw cron action: run, jobId: ai-engineering-digest
```

## Editing

- **Change styling:** Edit `style.css`
- **Change HTML structure:** Edit `scripts/newsletter_generate.py`
- **Change cron schedule:** Update via OpenClaw cron
- **Change research prompts:** Update the agent prompts in this pipeline (managed by Pepe)
