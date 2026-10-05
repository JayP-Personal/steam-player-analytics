# Roadmap

Each milestone becomes a GitHub milestone and ends with a tagged release. Each checkbox is sized as one issue and one pull request. Task prefixes follow [Conventional Commits](https://www.conventionalcommits.org/) and are the PR titles.

**Guiding constraint:** postings disappear when they close and can't be backfilled, so the collector goes live first and everything else is built while it runs.

---

## v0.1 — Ingestion

**Goal:** a daily Airflow DAG lands every tracked company's job board in Snowflake, reliably and unattended.

- [ ] `docs(adr)`: 0003 company sampling frame (which companies, how chosen, what it means for the results)
- [ ] `feat(seeds)`: company list with job board platform and board slug
- [ ] `feat(snowflake)`: raw table for job board responses (`VARIANT` payload, company, platform, fetched_at)
- [ ] `feat(ingest)`: Greenhouse client with retries, rate limiting and tests
- [ ] `feat(ingest)`: Lever client with tests
- [ ] `feat(ingest)`: Ashby client with tests
- [ ] `feat(airflow)`: daily DAG that loads all boards into Snowflake
- [ ] `feat(airflow)`: failure alerting
- [ ] `chore(release)`: v0.1.0

**Done when:** the DAG has run 7 days in a row without manual intervention.

---

## v0.2 — Staging

**Goal:** one clean, tested table of postings regardless of which platform they came from.

- [ ] `feat(dbt)`: sources with freshness tests on the raw table
- [ ] `feat(dbt)`: one staging model per platform, flattening JSON
- [ ] `feat(dbt)`: unified `stg_postings` across platforms
- [ ] `feat(dbt)`: deduplication of multi-location and reposted listings
- [ ] `docs(adr)`: how a "posting" is defined (and what counts as a repost)
- [ ] `chore(release)`: v0.2.0

**Done when:** every model has a stated grain, a primary-key test and column descriptions.

---

## v0.3 — Posting lifecycle

**Goal:** know when each posting opened, changed and closed.

- [ ] `feat(dbt)`: snapshot of postings to capture edits (title, salary, remote status)
- [ ] `feat(dbt)`: `fct_posting_lifecycle` with first seen, last seen, closed flag
- [ ] `feat(dbt)`: `fct_collection_gaps` (expected vs. observed fetches per board per day)
- [ ] `docs(adr)`: handling postings already open when collection began (left truncation) and still open at analysis time (right censoring)
- [ ] `chore(release)`: v0.3.0

---

## v0.4 — Enrichment

**Goal:** turn free-text postings into analyzable features.

- [ ] `feat(dbt)`: title normalization into role families (data, ML, software, analyst, …)
- [ ] `feat(dbt)`: seniority level from title
- [ ] `feat(dbt)`: remote / hybrid / onsite
- [ ] `feat(dbt)`: salary range parsing where disclosed
- [ ] `feat(skills)`: keyword dictionary for skill extraction, with AI/LLM skills flagged
- [ ] `analysis(skills)`: hand-label ~200 postings; measure extractor precision and recall
- [ ] `feat(dbt)`: `mart_postings_daily` analysis panel
- [ ] `chore(release)`: v0.4.0

---

## v0.5 — Analysis

**Goal:** answer the question, with honest uncertainty.

- [ ] `analysis(ai-demand)`: share of postings requiring AI skills over time, by role family and seniority, with confidence intervals
- [ ] `analysis(time-to-close)`: Kaplan–Meier curves by role family
- [ ] `analysis(time-to-close)`: Cox proportional hazards model; check its assumptions
- [ ] `analysis`: robustness checks (sampling frame, extractor error, definition choices)
- [ ] `docs`: `analysis/reports/findings.md` — methods, results, uncertainty, limitations
- [ ] `chore(release)`: v0.5.0

---

## v1.0 — Presentation

- [ ] `feat(tableau)`: dashboard published to Tableau Public; screenshots in `docs/images/`
- [ ] `docs`: README rewritten around the findings
- [ ] `docs`: external writeup (blog or LinkedIn) linked from README
- [ ] `chore(release)`: v1.0.0

---

## Later / ideas

- Combine with state WARN Act layoff notices: which companies cut in one area while hiring in another?
- Salary trends under pay-transparency laws
- Forecasting posting volume, with backtesting