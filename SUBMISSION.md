# Portal submission - Intelligent Contracts (Builder track)

Two standalone primitives, submit as two contributions.

Repo: https://github.com/phu1271997/quorum-oracles
Network: GenLayer Studionet (chain id 61999)

---

## 1. FigureQuorum

**Title**
FigureQuorum - consensus unit-exact number from independent prose reports

**Address**
`0xb4fB07b7242Cd9ad1E35dEB9553e84e4D6622C3b`

**Description (<1000 chars)**
FigureQuorum is a reusable GenLayer oracle primitive that turns several
independently published prose reports into one number the whole validator set
agrees on. A caller opens a round with 3 to 7 source documents, each pinned to a
GitHub commit and a SHA-256 hash. Every validator fetches the same bytes,
confirms the hash, and asks its own LLM to read each document and lift out the
figure for a named metric, with a verbatim supporting quote. Consensus is on the
meaning of each reading, not JSON shape: a validator agrees only when its own
independent audit finds every reading is the value and unit the full source
actually supports. The contract then folds the readings deterministically with
exact integer unit conversion, a median-absolute-deviation outlier filter and a
trimmed mean, and stores the round on chain. Parameterised by (repo, subject,
metric, unit family), so one deployment serves KPI, ESG, lab or audit figures.

**Verification (<500 chars)**
Deployed on Studionet at 0xb4fB07b7242Cd9ad1E35dEB9553e84e4D6622C3b (deploy
Result: SUCCESS, get_state reads back the configured metric). Source, README,
design notes and deterministic tests (unit conversion, MAD outlier rejection,
trimmed mean, source-commitment validation) at
https://github.com/phu1271997/quorum-oracles

---

## 2. ClaimQuorum

**Title**
ClaimQuorum - consensus categorical verdict from independent prose reports

**Address**
`0x078B1AAf31250b29260b33465D63Cf979fbaE399`

**Description (<1000 chars)**
ClaimQuorum is a reusable GenLayer adjudication primitive. Where FigureQuorum
folds numbers, ClaimQuorum folds judgements. A caller opens a batch with one
fixed question and 3 to 7 source documents, each pinned to a GitHub commit and a
SHA-256 hash. Every validator fetches the same bytes, confirms the hash, and
asks its own LLM to read each document and cast one labelled vote from a small
fixed ballot, with a strength and a verbatim quote, or to abstain. Consensus is
on the meaning of each vote, not JSON shape: a validator agrees only when its
own independent audit finds each label is the one that source genuinely
supports. The contract resolves the batch deterministically by
confidence-weighted plurality, flags a dispute when the winning margin is thin,
and stores the batch on chain. Parameterised by (repo, question, labels), so one
deployment serves fact checks, claim triage or eligibility rulings.

**Verification (<500 chars)**
Deployed on Studionet at 0x078B1AAf31250b29260b33465D63Cf979fbaE399 (deploy
Result: SUCCESS, get_state reads back the configured question and ballot).
Source, README, design notes and deterministic tests (weighted plurality,
dispute margin, abstain handling, verbatim-quote enforcement) at
https://github.com/phu1271997/quorum-oracles
