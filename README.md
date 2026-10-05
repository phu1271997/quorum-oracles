# Quorum Oracles

Two standalone **GenLayer Intelligent Contract primitives** that turn several
independently published prose reports into one answer the whole validator set
agrees on. Both pin every source document by commit and SHA-256, let each
validator read the full text with its own LLM, and reach consensus on the
**meaning** of each reading rather than on JSON shape.

| Contract | File | Folds | Consensus output |
|---|---|---|---|
| **FigureQuorum** | [`contracts/figure_quorum.py`](contracts/figure_quorum.py) | numbers | unit-exact integer with a MAD outlier filter + trimmed mean |
| **ClaimQuorum** | [`contracts/claim_quorum.py`](contracts/claim_quorum.py) | judgements | confidence-weighted plurality label with a dispute test |

They are siblings: same source-commitment and validation backbone, two
different *aggregation* heads. Use FigureQuorum when the truth is a quantity,
ClaimQuorum when the truth is a category.

## Why this is a primitive, not a demo

- **Parameterised at construction**, so one deployment serves many jobs.
  FigureQuorum takes `(source_repo, subject, metric, family)`; ClaimQuorum takes
  `(source_repo, question, labels)`. Nothing about the use case is hardcoded.
- **Non-determinism is the point.** Strip the web fetch and the LLM reading and
  there is no primitive left - the whole value is distilling a defensible answer
  from unstructured human text.
- **The validator checks meaning.** Each validator re-fetches every document,
  re-hashes the bytes, re-parses the proposal deterministically, and then runs
  an *independent* LLM audit that answers true for a row only if the reading is
  actually the value/label that full source supports, backed by its verbatim
  quote. Two nodes that would reach different conclusions do **not** agree. A
  row that merely has the right JSON keys does not pass.

## How consensus works (both contracts)

1. A caller opens a round/batch with 3..7 sources. Each source is
   `{id, url, sha256}` and the `url` must be a **commit-pinned** raw GitHub file
   inside the fixed `source_repo`, under `datasets/<period>/...md`.
2. **Leader** fetches each document, verifies size and `sha256`, then asks its
   LLM to read every document independently and produce one structured row per
   document (a MEASURED/MISSING figure, or a labelled vote / ABSTAIN).
3. The contract **parses the proposal deterministically** - strict field set,
   exact numeric/label grammar, and every quote must be a verbatim span of the
   source. Anything off-grammar is rejected before consensus.
4. **Validators** repeat the fetch + hash + deterministic parse, then run a
   second independent LLM pass that audits each row against the full source. The
   leader proposal is accepted only if every row passes for every validator.
5. The accepted readings are folded **deterministically** - exact integer unit
   conversion + MAD outlier rejection + trimmed mean (FigureQuorum), or a
   confidence-weighted tally + margin/dispute test (ClaimQuorum) - and the full
   round is stored on chain as canonical JSON.

The split matters: subjective work (reading messy prose) goes through the LLM
jury; objective work (arithmetic, tallies, thresholds) is pure Python that is
byte-identical on every node.

## Public API

**FigureQuorum**
- `open_round(period: str, sources_json: str)` - run a new round.
- `get_latest() -> dict`, `get_round(index) -> dict`, `get_round_by_period(period) -> dict`
- `get_state() -> dict`

**ClaimQuorum**
- `open_batch(batch: str, sources_json: str)` - run a new batch.
- `get_latest() -> dict`, `get_round(index) -> dict`, `get_batch(batch) -> dict`
- `get_state() -> dict`

`sources_json` is a JSON array, e.g.:

```json
[
  {"id":"gauge-a","url":"https://raw.githubusercontent.com/<repo>/<40-hex-commit>/datasets/rain-2026-09-01/gauge-a.md","sha256":"<64 hex>"},
  {"id":"gauge-b","url":"https://raw.githubusercontent.com/<repo>/<40-hex-commit>/datasets/rain-2026-09-01/gauge-b.md","sha256":"<64 hex>"},
  {"id":"gauge-c","url":"https://raw.githubusercontent.com/<repo>/<40-hex-commit>/datasets/rain-2026-09-01/gauge-c.md","sha256":"<64 hex>"}
]
```

Pin the commit (not a branch) so the bytes can never change under the hash. See
[`datasets/README.md`](datasets/README.md) for how to compute digests and pin a
commit.

## Deployed on Studionet

| Contract | Address |
|---|---|
| FigureQuorum | `0xb4fB07b7242Cd9ad1E35dEB9553e84e4D6622C3b` |
| ClaimQuorum  | `0x078B1AAf31250b29260b33465D63Cf979fbaE399` |

Network: GenLayer Studionet (chain id `61999`, RPC `https://studio.genlayer.com/api`).
Explorer: <https://explorer-studio.genlayer.com/address/0xb4fB07b7242Cd9ad1E35dEB9553e84e4D6622C3b>

## Develop

```bash
pip install -r requirements.txt          # genlayer-py for deploy, pytest for tests
python3 scripts/deploy.py both --check-only   # validate both schemas, no key needed

source ~/.genlayer/env.sh                 # exports GENLAYER_PRIVATE_KEY
python3 scripts/deploy.py both            # deploy both to studionet

pytest -q                                 # deterministic aggregation tests
```

## Tests

[`tests/test_logic.py`](tests/test_logic.py) exercises the deterministic core
without a GenVM: exact unit conversion, MAD outlier rejection and the trimmed
mean, insufficient-data handling, weighted-plurality resolution vs. dispute, the
ABSTAIN path, and source-commitment validation (bad repo, bad hash grammar,
duplicate ids). These are the parts that must be byte-identical across
validators, so they are the parts worth pinning down in tests.

## License

MIT - see [LICENSE](LICENSE).
