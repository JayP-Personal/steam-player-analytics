# 0003. Company sampling frame

- **Status:** Accepted
- **Date:** 2026-10-05

## Context
Results describe whichever companies are tracked, so the selection must be reproducible and its gaps measurable. Job board platforms don't publish customer lists, and many large employers use Workday, which this project doesn't collect.

## Options considered
1. **Hand-pick well-known companies:** fast, but biased and impossible to reproduce.
2. **Use an open-source board inventory directly:** thousands of boards immediately, but no defined population and no way to measure what's missing.
3. **Start from published company lists, then find each company's board:** reproducible and lets coverage be measured; more upfront work.

## Decision
Option 3. Candidates come from sources below, tagged by stage (early, growth, public). Boards are found via the ats-scrapers inventory (MIT; combined companies.csv, downloaded 2026-10-07), slug guessing, then manual lookup., and every board is verified against its live API. Companies included before collection starts form a frozen core cohort for trend analysis.

## Sources:
Candidates come from the 150 largest active, hiring YC companies from 2024+ batches (by team size), the Forbes Cloud 100 (2025), and S&P 500 companies in the Information Technology sector plus the Interactive Media & Services and Broadline Retail sub-industries, retrieved 2026-10-05.

## Consequences
- Every candidate's platform is recorded, including unsupported ones, so coverage can be reported per stage.
- Large enterprises are underrepresented; results are reported by stage.
- Companies added later, or from new platforms, are analyzed as separate cohorts.