# Tech Hiring Signals

> **Status:** 🚧 v0.1 in progress. Daily job-posting collection is being built.

## The question

**How is AI changing what tech companies hire for?**

Company job boards only show what's open today. Once a role is filled or pulled, the posting disappears. This project takes a daily snapshot of public job boards to build a history of postings, then uses it to answer:

1. **AI skill demand:** What share of data, engineering and analyst postings ask for AI or LLM skills, and how fast is that share changing?
2. **Seniority mix:** Are entry-level roles shrinking relative to senior ones?
3. **Time to close:** How long do different kinds of roles stay open? (Survival analysis)

## Key findings

_Coming in v0.5. This section will lead with the headline result, one chart, and a link to the dashboard._

## Architecture

```
Public job boards ──► Airflow (daily) ──► Snowflake RAW ──► dbt (staging → marts) ──► Tableau
 Greenhouse / Lever / Ashby                 raw JSON          tested, documented        dashboard
                                                                     │
                                                                     └──► Python stats analysis
```

| Layer | Tool | Role |
|---|---|---|
| Orchestration | Airflow | Daily collection, retries, alerting |
| Storage | Snowflake | Raw JSON landing zone and warehouse |
| Transformation | dbt | Cleaning, deduplication, posting history (snapshots), data tests |
| Analysis | Python | Trend estimation, survival models |
| Visualization | Tableau | Public dashboard |

## Data

Postings come from the public job board endpoints that companies use to display openings on their own career sites. The set of companies included, and what that means for how far the results generalize, is documented in the decision records.

Two caveats apply to every result in this project:

- **The sample is not all employers.** Companies using these platforms skew toward tech and venture-backed firms.
- **A closed posting is not necessarily a filled role.** Postings also close when a role is cancelled or put on hold.

## Project docs

- [Roadmap](docs/roadmap.md)
- [Architecture decision records](docs/adr/)

## License

[MIT](LICENSE). This repository contains code only. No posting data or personal information is stored in git.
