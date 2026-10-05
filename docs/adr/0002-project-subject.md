# 0002. Change project subject from Steam player counts to tech job postings

- **Status:** Accepted
- **Date:** 2026-10-05

## Context
The project began as an analysis of Steam games, asking what predicts whether a game keeps its players after launch. The question was technically sound, but its audience is narrow: a reviewer has to care about games to care about the answer. Only a repo skeleton existed, so switching now costs little.

## Options considered
1. **Keep Steam.** Plan already outlined; niche audience.
2. **AI-era tech hiring, from public job board postings.** Every tech interviewer has a stake in the answer. Postings disappear when they close, so data must be collected daily, which gives the orchestration layer real work.
3. **Grid electricity demand vs. data center growth (EIA API).** Strong causal-inference showcase, but less connected to the target audience.

## Decision
Option 2. The project now asks how AI is changing what tech companies hire for, using daily snapshots of public Greenhouse, Lever and Ashby job boards.

## Consequences
- The stack chosen in [0001](0001-data-stack.md) is unchanged.
- The planned survival analysis carries over: time until a posting closes replaces time until a game loses its players.
- New risks: the companies sampled are not representative of all employers, and a closed posting is not necessarily a filled role. Both get their own decision records and are discussed in the analysis writeup.
- Collection must start quickly, since closed postings cannot be backfilled.
- Repository renamed from `steam-player-analytics` to `tech-hiring-signals`.
