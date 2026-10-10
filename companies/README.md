   # Companies

   How the tracked companies were chosen (see [ADR 0003](../docs/adr/0003-company-sampling-frame.md)):

   1. `candidates.csv`: 330 companies from three published lists
   2. `board_proposals.csv`: possible job boards (inventory match or slug guess)
   3. `verified_boards.csv`: each board checked against its live API

   | Stage  | Candidates | Board found | Not found |
   |--------|-----------:|------------:|----------:|
   | early  | 150 | 69 | 81 |
   | growth | 100 | 71 | 29 |
   | public |  80 | 11 | 69 |
   | **total** | **330** | **151** | **179** |

   "Not found" means no board was found automatically. Unmatched companies were not
   looked up by hand, so coverage figures are lower bounds.