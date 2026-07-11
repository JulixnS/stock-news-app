# Stock News Sentiment App — Build Checklist

Scrape Yahoo Finance news per ticker, score bull/bear sentiment with FinBERT, serve scores over a FastAPI API, and email a daily "potential picks" digest. Runs as one long-lived process on a free-tier Oracle VM. Built to add more news sources later without reworking the pipeline.

**Build order = top to bottom.** Each phase leaves you with something runnable. Check boxes as you go.

> ⚠️ Not financial advice. This is a signal-generation toy, not an investment system. Bake a disclaimer into every digest.

---

## 0. Lock the decisions first

Recommended defaults are in **bold** — take them unless you have a reason not to. Fill the rest into the decisions log at the bottom.

- [ ] Ticker list: start with **5–10** you actually follow (scale later)
- [ ] Articles per ticker per run (`n`): **10**
- [ ] Run frequency: **daily** (one digest per day)
- [ ] Storage: **SQLite** (history is required for "did the score move vs. yesterday" — a flat file won't cut it)
- [ ] Sentiment input granularity: **headline + RSS summary** (better than headline-only, free from RSS)
- [ ] Daily delivery channel: **email via connected Gmail** (alt: SMTP, Telegram bot, dashboard-only)
- [ ] "Pick" rule — what makes a ticker show up in the digest. Default: **top N by bull score where `article_count ≥ 3` and `avg_confidence ≥ 0.6`, tie-broken by day-over-day score increase**
- [ ] Process model: **single long-running FastAPI process** with in-app scheduler (load FinBERT once; do NOT reload per run)

## 1. Project scaffold & environment

- [ ] Create a virtualenv, add `requirements.txt`
- [ ] Install deps: `fastapi`, `uvicorn`, `feedparser`, `transformers`, `torch` (CPU), `apscheduler`, `pydantic`, `httpx`
- [ ] Lay out the package structure:
  - [ ] `sources/` — news source adapters
  - [ ] `sentiment.py` — FinBERT scorer
  - [ ] `store.py` — SQLite read/write
  - [ ] `pipeline.py` — fetch → score → aggregate → store
  - [ ] `selection.py` — ranking / "today's picks"
  - [ ] `notify.py` — daily digest delivery
  - [ ] `scheduler.py` — schedules the daily run
  - [ ] `api.py` (or extend `app.py`) — FastAPI endpoints
- [ ] Add `.gitignore` (`.venv/`, `__pycache__/`, `*.db`, secrets)
- [ ] `config.py` or `.env` for ticker list, `n`, email settings, thresholds

## 2. News source layer (built for multiple sites)

- [ ] Define a normalized `Article` shape: `ticker, title, url, published, snippet, source`
- [ ] Define a `NewsSource` interface: `fetch(ticker, n) -> list[Article]` (so adding a site later = one new adapter)
- [ ] Implement `sources/yahoo.py` using the **Yahoo Finance RSS feed** — no HTML/JS scraping needed:
      `https://feeds.finance.yahoo.com/rss/2.0/headline?s=TICKER&region=US&lang=en-US`
  - [ ] Parse with `feedparser` → title, link, published date, summary
  - [ ] Return the latest `n` normalized `Article`s
- [ ] Error handling: empty feed, malformed entries, network errors, timeouts
- [ ] Polite fetching: timeout + small delay/backoff; set a real User-Agent
- [ ] Check Yahoo's `robots.txt` / terms; RSS is the more defensible path — note your call in the log
- [ ] De-dupe by article URL so the same story isn't scored twice across runs
- [ ] (Later) add a second adapter to prove the interface holds — no pipeline changes should be needed

## 3. Sentiment scoring (FinBERT)

- [ ] Load `ProsusAI/finbert` **once** at process startup (module-level, not per article)
- [ ] `score_sentiment(text) -> {label, confidence}` returning positive/negative/neutral + confidence
- [ ] Map FinBERT positive/negative/neutral → your bull/bear/neutral labels
- [ ] Feed `title + " " + snippet` (per the granularity decision)
- [ ] Sanity-check on a handful of hand-picked headlines (obvious good/bad news) before trusting it

## 4. Storage (SQLite)

- [ ] Schema: a `scores` table — `ticker, run_date, bull_score, article_count, avg_confidence, created_at`
- [ ] (Optional) an `articles` table — cached scored articles for de-dupe + audit
- [ ] `store.py`: write a run's results; read latest score per ticker; read previous run's score (for day-over-day)
- [ ] Confirm history accumulates across runs (needed for trend + pick logic)

## 5. Pipeline integration

- [ ] `pipeline.py`: for each ticker → fetch articles → score each → aggregate to one bull score + confidence + count
- [ ] Aggregation method (average, or majority vote, weighted by confidence) — pick and note it
- [ ] Loop over all tickers; **one bad ticker must not kill the batch** (catch + log per ticker)
- [ ] Write per-ticker results to SQLite with a run timestamp
- [ ] Run summary log: N tickers processed, M articles scored, errors
- [ ] Run the whole pipeline once by hand and eyeball the stored rows

## 6. Selection — "today's picks"

- [ ] `selection.py`: apply the pick rule from §0 against the latest scores
- [ ] Compute day-over-day delta (today's score vs. previous run) for tie-breaks / momentum
- [ ] Return a ranked shortlist with the reason each ticker qualified (score, count, delta)
- [ ] Handle the empty case gracefully (no ticker clears the bar → say so, don't crash)

## 7. FastAPI endpoints

- [ ] `GET /tickers/{ticker}` — latest bull/bear score + article count + confidence
- [ ] `GET /picks` — today's ranked shortlist (the digest content, on demand)
- [ ] `GET /tickers/{ticker}/history` — score over time for trend
- [ ] `POST /refresh` (optional) — trigger a pipeline run manually
- [ ] `GET /health` — liveness check
- [ ] Return proper JSON (typed Pydantic responses), not bare strings
- [ ] Confirm FinBERT is loaded once at app startup and reused across requests

## 8. Daily delivery

- [ ] `notify.py`: format the picks shortlist into a readable digest (ticker, score, why, top headline + link)
- [ ] Include the "not financial advice" disclaimer
- [ ] Send via the chosen channel (Gmail / SMTP / Telegram)
- [ ] Handle send failures loudly (log; don't silently swallow)
- [ ] Send yourself one real test digest end-to-end

## 9. Scheduling (in-process)

- [ ] `scheduler.py`: APScheduler job inside the FastAPI process → run pipeline, then send digest, at your chosen time
- [ ] Reuses the already-loaded FinBERT model (the reason for the single-process design)
- [ ] Confirm the scheduled job fires and produces both stored rows and an email
- [ ] Decide behavior if a run overlaps or the previous run failed

## 10. Oracle VM deployment

- [ ] Create Oracle Cloud Always Free account
- [ ] Provision an Ampere A1 (ARM) instance within current free-tier limits (give it enough RAM for FinBERT + torch)
- [ ] SSH in; confirm `uname -m` shows `aarch64`
- [ ] Install Python + pip + system deps
- [ ] `pip install` the requirements; verify ARM wheels for `torch`/`transformers` resolve
- [ ] Move code onto the VM (git clone) and set secrets/env there
- [ ] Run the FastAPI process under a supervisor (systemd service) so it restarts on reboot/crash
- [ ] Do a manual end-to-end run on the VM before trusting the schedule
- [ ] Confirm logs land somewhere you can read later
- [ ] Guard against idle reclamation if the free tier risks it

## 11. Validation

- [ ] Spot-check sentiment scores against your own read of a few articles
- [ ] Compare headline-only vs. headline+snippet scoring on a sample; note the difference
- [ ] Gut-check: do a few days of digests line up with actual next-day price moves? (sanity check, not a backtest)
- [ ] Verify the pick rule surfaces sensible tickers (tune thresholds if it's too noisy or too quiet)

## 12. Stretch goals (optional)

- [ ] Add a second news source adapter (prove the multi-site design)
- [ ] Simple dashboard (static HTML table / small frontend) showing scores + trends
- [ ] Compare FinBERT against a baseline (VADER, or TF-IDF + logistic regression)
- [ ] Chunk full article bodies and average vs. headline+snippet; note the quality delta
- [ ] Weeks-long trend charts per ticker
- [ ] Alert on large single-day sentiment swings, not just the daily digest

---

**Notes / decisions log** (fill in as you go):

- Tickers tracked:
- `n` / frequency / pick-rule thresholds:
- Delivery channel + why:
- Aggregation method:
- Yahoo RSS vs. ToS call:
