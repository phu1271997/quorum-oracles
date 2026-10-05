"""Deterministic-core tests for both primitives (off-chain, no GenVM).

conftest.py installs a `genlayer` stub before these imports run.
"""
import pytest

from contracts import figure_quorum as fq
from contracts import claim_quorum as cq

UE = fq.gl.vm.UserError

REPO = "owner/repo"
COMMIT = "a" * 40


def _url(period, name):
    return f"https://raw.githubusercontent.com/{REPO}/{COMMIT}/datasets/{period}/{name}.md"


def _src(sid, period, name):
    return {"id": sid, "url": _url(period, name), "sha256": "b" * 64}


# ---------------------------------------------------------------- FigureQuorum

def test_unit_conversion_is_exact_integer():
    # length base is micrometre: 1 mm = 1000 um, 2.5 cm = 25000 um, 0.001 km = 1000000 um
    assert fq._to_base("1", "mm", "length") == 1000
    assert fq._to_base("2.5", "cm", "length") == 25000
    assert fq._to_base("0.001", "km", "length") == 1000000
    # mass base is milligram: 1 kg = 1_000_000 mg
    assert fq._to_base("1", "kg", "mass") == 1000000


def test_to_base_rejects_bad_grammar():
    with pytest.raises(UE):
        fq._to_base("12.3456", "mm", "length")   # too many decimals
    with pytest.raises(UE):
        fq._to_base("5", "in", "length")          # unit not in family


def _readings(values_units):
    rows = []
    for i, vu in enumerate(values_units):
        if vu is None:
            rows.append({"index": i, "decision": "MISSING", "value": "", "unit": "", "quote": "", "base": None})
        else:
            v, u = vu
            rows.append({"index": i, "decision": "MEASURED", "value": v, "unit": u,
                         "quote": "q" * 12, "base": fq._to_base(v, u, "length")})
    return {"rows": rows}


def test_fold_drops_outlier_and_trims_mean():
    # three tight readings around 10 mm plus one gross outlier at 900 mm
    readings = _readings([("10", "mm"), ("11", "mm"), ("9", "mm"), ("900", "mm")])
    out = fq._fold("p1", "subj", "length", readings)
    assert out["status"] == "READY"
    assert out["measured_count"] == 4
    assert out["kept_count"] == 3
    assert out["dropped_indexes"] == [3]
    # trimmed mean of 10,11,9 mm = 10 mm = 10000 um
    assert out["consensus_base"] == 10000
    assert out["base_unit"] == "um"


def test_fold_insufficient_when_fewer_than_three_measured():
    readings = _readings([("10", "mm"), ("11", "mm"), None])
    out = fq._fold("p1", "subj", "length", readings)
    assert out["status"] == "INSUFFICIENT"
    assert out["consensus_base"] is None


def test_figure_sources_validation():
    good = [_src("a", "rain-2026-09-01", "a"), _src("b", "rain-2026-09-01", "b"),
            _src("c", "rain-2026-09-01", "c")]
    assert len(fq._read_sources(good, REPO, "rain-2026-09-01")) == 3
    with pytest.raises(UE):
        fq._read_sources(good[:2], REPO, "rain-2026-09-01")          # too few
    with pytest.raises(UE):
        fq._read_sources(good, "other/repo", "rain-2026-09-01")      # wrong repo
    dupe = [_src("a", "p", "a"), _src("a", "p", "b"), _src("c", "p", "c")]
    with pytest.raises(UE):
        fq._read_sources(dupe, REPO, "p")                            # duplicate id
    badhash = [dict(_src("a", "p", "a"), sha256="xyz"), _src("b", "p", "b"), _src("c", "p", "c")]
    with pytest.raises(UE):
        fq._read_sources(badhash, REPO, "p")                         # bad sha grammar


# ----------------------------------------------------------------- ClaimQuorum

LABELS = ["SUPPORTED", "REFUTED", "UNVERIFIABLE"]


def _votes(items):
    rows = []
    for i, it in enumerate(items):
        if it is None:
            rows.append({"index": i, "label": cq.ABSTAIN, "weight": 0, "quote": ""})
        else:
            label, weight = it
            rows.append({"index": i, "label": label, "weight": weight, "quote": "q" * 12})
    return {"votes": rows}


def test_resolve_weighted_plurality():
    parsed = _votes([("SUPPORTED", 90), ("SUPPORTED", 80), ("REFUTED", 10)])
    out = cq._resolve("b1", "q", LABELS, parsed)
    assert out["status"] == "RESOLVED"
    assert out["consensus_label"] == "SUPPORTED"
    assert out["participating"] == 3
    assert out["tally"]["SUPPORTED"] == 170
    assert out["agreement_pct"] == 170 * 100 // 180


def test_resolve_dispute_when_margin_too_thin():
    parsed = _votes([("SUPPORTED", 50), ("REFUTED", 48), ("UNVERIFIABLE", 5)])
    out = cq._resolve("b1", "q", LABELS, parsed)
    assert out["status"] == "DISPUTED"
    assert out["consensus_label"] is None


def test_resolve_insufficient_with_abstentions():
    parsed = _votes([("SUPPORTED", 90), None, None])
    out = cq._resolve("b1", "q", LABELS, parsed)
    assert out["status"] == "INSUFFICIENT"
    assert out["abstained"] == 2
    assert out["participating"] == 1


def test_read_labels_rejects_abstain_and_dupes():
    assert cq._read_labels(LABELS) == LABELS
    with pytest.raises(UE):
        cq._read_labels(["SUPPORTED"])                 # too few
    with pytest.raises(UE):
        cq._read_labels(["SUPPORTED", "ABSTAIN"])      # ABSTAIN not allowed
    with pytest.raises(UE):
        cq._read_labels(["SAME", "SAME"])              # duplicate


def test_parse_votes_requires_verbatim_quote():
    docs = ["the service met its SLA every day this month, fully"]
    good = {"votes": [{"index": 0, "label": "SUPPORTED", "weight": 80,
                       "quote": "the service met its SLA"}]}
    assert cq._parse_votes(good, docs, LABELS)["votes"][0]["label"] == "SUPPORTED"
    bad = {"votes": [{"index": 0, "label": "SUPPORTED", "weight": 80,
                      "quote": "this quote is not in the document at all"}]}
    with pytest.raises(UE):
        cq._parse_votes(bad, docs, LABELS)
