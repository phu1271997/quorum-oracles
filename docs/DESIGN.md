# Design notes

## The shared backbone

Both contracts answer the same hard question in two different shapes: *given
several independent written reports, what is the one answer the network should
commit to?* The parts that are identical are the parts that make the answer
trustworthy:

1. **Source commitment.** A caller cannot point the oracle at an arbitrary URL.
   Every source must live in the contract's fixed `source_repo`, under
   `datasets/<round>/`, pinned to a 40-hex commit, and carry a SHA-256 that must
   match the served bytes. This removes "the page changed under us" and "the
   leader and validators saw different text" as failure modes.

2. **Independent reading.** The leader asks its LLM to read each document on its
   own and emit a strict per-document row. The documents are explicitly framed
   as untrusted data, never instructions (prompt-injection defence).

3. **Deterministic parse.** Before anything reaches consensus the contract
   enforces an exact grammar: a fixed field set, a tight numeric/label syntax,
   and every quote must be a verbatim substring of the source. Off-grammar
   proposals are rejected deterministically.

4. **Meaning-level validation.** Each validator re-fetches, re-hashes,
   re-parses, and then runs a *second, independent* LLM audit that answers true
   for a row only if the reading is the value/label the full source actually
   supports - and it is told to scrutinise negatives (MISSING / ABSTAIN) as hard
   as positives. The proposal is accepted only if every row passes. This is what
   keeps it from being a format-only validator: two validators who would read a
   source differently will not agree.

5. **Deterministic fold.** The accepted readings are aggregated with pure Python
   so the final number/label is byte-identical on every node.

## The two heads

### FigureQuorum - robust numeric fold

- Exact integer unit conversion via per-family scale tables (length to
  micrometre, mass to milligram, volume to microlitre). No floats ever touch
  chain state; a decimal string is folded as `int(whole+frac) * scale //
  10**len(frac)`.
- Outlier rejection uses the **median absolute deviation**: centre on the
  median, drop any reading more than `3 * MAD` from it (with a small relative
  floor so a zero MAD does not reject everything), then report the **trimmed
  mean** of the survivors. MAD is the standard robust-statistics choice and
  needs no tuning per metric.
- `status` is `READY` only with >= 3 surviving inliers, else `INSUFFICIENT`.

### ClaimQuorum - weighted categorical fold

- Each source casts one ballot label plus a self-reported strength (1..100), or
  `ABSTAIN` with weight 0.
- Resolution is **confidence-weighted plurality**: tally weight per label, take
  the winner, and require the winning margin to be at least one fifth of the
  total cast weight. Otherwise the batch is `DISPUTED` (an honest "the sources
  do not agree" rather than a coin-flip). Fewer than 3 participating sources is
  `INSUFFICIENT`.
- `agreement_pct` exposes how concentrated the weight was behind the winner.

## State lifecycle

- Rounds/batches are append-only canonical-JSON entries in a `DynArray[str]`.
- A `TreeMap[str, str]` maps each period/batch slug to its round index and
  enforces single-use, so the same labelled round cannot be replayed.
- A per-contract `MAX_ROUNDS` cap bounds storage growth.
- Views return already-folded outcomes plus the full source and reading record,
  so a downstream contract can both trust the headline and re-audit the inputs.

## Deliberate non-goals

- No frontend - these are standalone primitives (the Intelligent Contracts
  track), meant to be imported by other contracts and dApps.
- The bundled `datasets/` files are illustrative shapes, not real feeds.
  Production use needs credibly governed, independently produced sources and a
  separate collusion-resistance story for the source set itself.
