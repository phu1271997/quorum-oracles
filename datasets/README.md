# datasets/

Source documents live here, grouped by round:

```
datasets/<period-or-batch>/<source-id>.md
```

Each file is an untrusted prose report. The contracts never run a file as
instructions - they only read it as data and lift out one figure (FigureQuorum)
or one labelled vote (ClaimQuorum).

## Pinning a source

A source entry passed to `open_round` / `open_batch` is:

```json
{"id": "gauge-a", "url": "https://raw.githubusercontent.com/<repo>/<commit>/datasets/<period>/gauge-a.md", "sha256": "<digest>"}
```

Rules enforced on chain:

- the `url` must sit inside the contract's fixed `source_repo`;
- the path must be `datasets/<period>/<id>.md`;
- the commit must be a full 40-hex **commit SHA**, never a branch, so the bytes
  cannot change under the hash;
- `sha256` must equal the SHA-256 of the exact bytes served.

## Computing a digest

```bash
# after committing the file and pushing
git rev-parse HEAD                       # the 40-hex commit to pin
shasum -a 256 datasets/rain-2026-09-01/gauge-a.md   # the digest to pin
```

The examples under `rain-2026-09-01/` (numeric) and `sla-2026-q3/`
(categorical) are illustrative report shapes, not real measurements. Replace
them with credibly governed, independently produced feeds before using either
primitive for anything that matters.
