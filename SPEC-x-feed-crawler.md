# AI Engineering Identifier — X Feed Crawler Spec

## Purpose

Automated cronjob that crawls Pablo's X/Twitter feed every 2 hours, identifies AI Engineering-relevant content, and maintains a local trend ledger. The ledger tracks topics over time, detects trends based on source diversity, and produces trend candidates for future integration with the AI Engineering Digest email.

**This is a standalone product under active iteration — NOT yet integrated with the AI Digest email.**

## What It Identifies

Content relevant to a Software Engineer / AI Engineer who needs to stay current:

- **Models** — New AI model releases, benchmarks, capabilities
- **SDKs** — AI/ML libraries, client SDKs, API wrappers
- **Frameworks** — AI/ML frameworks, agent frameworks, orchestration tools
- **SaaS** — AI platforms, hosted services, API products
- **Tools** — Developer tools, coding assistants, IDEs, agents
- **Techniques** — AI engineering patterns, best practices, architectures
- **Infrastructure** — Inference, training, deployment, serving
- **Repositories** — AI Engineering tools, open source libraries, skills, tools

Everything else (politics, sports, entertainment, ads, non-tech) is filtered out.

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     OpenClaw Cron Job                         │
│                   (every 2 hours, ET)                         │
└──────────────┬───────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────┐
│  Stage 1: CRAWL                                              │
│                                                              │
│  • Open X via OpenClaw browser CLI (user profile)            │
│  • Check login status — abort + notify if session expired    │
│  • Scroll feed, extract posts via DOM (JS evaluate)          │
│  • Target: ~100 posts per crawl                              │
│  • Dedup against seen_posts in ledger                        │
│  • Output: list of new, unseen posts                         │
└──────────────┬───────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────┐
│  Stage 2: CLASSIFY (Gemma 4 12b — local, via Ollama)         │
│                                                              │
│  • Batch new posts (20 per batch) to Gemma                   │
│  • Gemma filters for AI Engineering relevance                │
│  • Returns: category, summary, topic keywords                │
│  • Irrelevant posts are discarded                            │
│  • Output: list of relevant posts with metadata              │
└──────────────┬───────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────┐
│  Stage 3: MATCH + TREND (Gemma 4 12b — local, via Ollama)    │
│                                                              │
│  • Compare relevant posts against existing ledger entries    │
│  • Gemma decides: match existing topic OR create new topic   │
│  • Update matched entries: post_count++, add source, merge   │
│    new characteristics                                       │
│  • Create new entries for genuinely new topics               │
│  • Recalculate trend flags: sources >= threshold → is_trend  │
│  • Output: updated ledger                                    │
└──────────────┬───────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────┐
│  Stage 4: NOTIFY                                             │
│                                                              │
│  • Send Telegram summary to Pablo                            │
│  • Include: new topics, updated topics, active trends        │
│  • Alert on errors: session expired, browser crash           │
└──────────────────────────────────────────────────────────────┘
```

## Ledger Schema

**File:** `~/.openclaw/workspace/memory/ai-feed-ledger.json`

```json
{
  "entries": [
    {
      "id": "a1b2c3d4e5f6g7h8",
      "topic": "Gemma 4 12B Release",
      "characteristics": [
        "Google's new 12B parameter open-weight model",
        "Multimodal capabilities including vision",
        "Runs locally on consumer hardware"
      ],
      "category": "model",
      "post_count": 12,
      "sources": ["@svpino", "@karpathy", "@simonw", "@lmsysorg"],
      "first_seen": "2026-06-04T09:00:00-04:00",
      "last_seen": "2026-06-04T17:00:00-04:00",
      "is_trend": true
    }
  ],
  "seen_posts": [
    {
      "url": "https://x.com/svpino/status/182736450",
      "crawl_date": "2026-06-04T09:00:00-04:00"
    }
  ],
  "crawl_log": [
    {
      "id": "crawl-20260604-0900",
      "timestamp": "2026-06-04T09:00:00-04:00",
      "posts_crawled": 95,
      "new_posts": 82,
      "relevant": 14,
      "new_entries": 8,
      "updated_entries": 6
    }
  ]
}
```

### Entry Fields

| Field | Type | Description |
|---|---|---|
| `id` | string | SHA-256 hash (first 16 chars) of lowercase topic name |
| `topic` | string | Human-readable topic name |
| `characteristics` | string[] | Key facts extracted by Gemma — used for fuzzy matching in future crawls |
| `category` | enum | `model`, `sdk`, `framework`, `saas`, `tool`, `technique`, `infrastructure` |
| `post_count` | int | Total unique posts seen about this topic (never counts same post twice) |
| `sources` | string[] | Unique X handles that posted about this topic |
| `first_seen` | ISO 8601 | When the topic first appeared in a crawl |
| `last_seen` | ISO 8601 | When the topic was last seen in a crawl |
| `is_trend` | bool | `true` when `len(sources) >= TREND_THRESHOLD` |

### Trend Detection

A topic becomes a **trend candidate** when it meets this condition:

> **3 or more unique X accounts** are posting about the same topic.

Two signals are tracked:
- **Volume** (`post_count`) — how much buzz exists (same source can post multiple times)
- **Breadth** (`sources`) — how many independent voices are talking about it (**this drives the trend flag**)

A topic with 20 posts from 1 person is NOT a trend. A topic with 5 posts from 5 people IS.

### Post Deduplication

Every crawled post URL is stored in `seen_posts`. Before sending posts to Gemma for classification, already-seen URLs are filtered out. This ensures:
- `post_count` only increments for genuinely new posts
- `sources` only adds handles from new posts
- Gemma never processes the same post twice
- Overlapping feed content between crawls doesn't inflate metrics

## Configurable Settings

All settings are defined as constants at the top of `scripts/x_feed_crawler.py`:

| Setting | Default | Description |
|---|---|---|
| `RETENTION_DAYS` | `7` | Days before entries and seen_posts are pruned |
| `TARGET_POSTS` | `100` | Posts to collect per crawl |
| `TREND_THRESHOLD` | `3` | Unique sources required to flag `is_trend` |
| `MAX_SCROLLS` | `30` | Safety cap on scroll iterations per crawl |
| `SCROLL_PAUSE` | `2.5` | Seconds between scrolls for content to load |
| `OLLAMA_URL` | `http://localhost:11434` | Ollama API endpoint |
| `OLLAMA_MODEL` | `gemma4:12b` | Local model for all classification and matching |
| `LEDGER_PATH` | `~/.openclaw/workspace/memory/ai-feed-ledger.json` | Ledger file location |
| `BROWSER_LABEL` | `xfeed` | Browser tab label for the crawl session |

## Cron Schedule

Every 2 hours during waking hours (Eastern Time):

```
8:00 AM, 10:00 AM, 12:00 PM, 2:00 PM, 4:00 PM, 6:00 PM, 8:00 PM
```

## Token Cost

**Claude tokens used: zero.** The entire pipeline runs locally:
- Post extraction: OpenClaw browser CLI + DOM JavaScript
- Classification: Gemma 4 12b via Ollama (local)
- Topic matching: Gemma 4 12b via Ollama (local)

The only external dependency is X itself (via the browser session).

## Browser & Session Strategy

- Uses OpenClaw browser with **user profile** (Pablo's existing cookies)
- X desktop sessions persist for weeks/months with cookie retention
- Every crawl starts with a login check — if the session expired:
  - Crawl is skipped
  - Telegram alert sent to Pablo: "X session expired, please re-login"
- Browser auto-start: if the browser isn't running, the script starts it
- Browser auto-recovery: if connection drops mid-crawl, retry with restart
- Tab cleanup: the `xfeed` tab is closed at the end of every crawl

**Cannot auto-login** — X uses captchas, 2FA, and bot detection. Manual re-login is the only safe option.

## Notification

After each crawl, send a Telegram message to Pablo with:
- New topics found
- Updated topics
- Active trends (if any)
- Errors (session expired, browser crash, Gemma failure)

## Error Handling

| Error | Behavior |
|---|---|
| Browser not running | Auto-start, retry |
| Browser crashes mid-crawl | Save whatever was collected, notify |
| X session expired | Skip crawl, send Telegram alert |
| Gemma unreachable | Skip classification, save raw posts for next run |
| Empty feed (no posts) | Log and exit cleanly |
| Feed exhausted before target | Use whatever was collected |

## Future Iterations (NOT in v1)

- Integration with AI Digest email (separate "Trending on X" section)
- Source weighting (verified accounts, known AI voices ranked higher)
- Trend ranking by importance (not just binary is_trend)
- Multiple feed tabs (Following + For You + Trending sidebar)
- Cross-platform sources (Reddit, HN, LinkedIn)
- Trend decay / staleness detection
