#!/usr/bin/env python3
"""Deploy the QuorumOracles contracts to a GenLayer network (default: studionet).

Usage:
    source ~/.genlayer/env.sh                 # exports GENLAYER_PRIVATE_KEY
    python3 scripts/deploy.py figure           # deploy FigureQuorum
    python3 scripts/deploy.py claim            # deploy ClaimQuorum
    python3 scripts/deploy.py both             # deploy both (default)
    python3 scripts/deploy.py both --check-only # schema check, no deploy

Reads the deployer key from GENLAYER_PRIVATE_KEY. Prints the deployed contract
address(es). Never hard-codes or prints the private key.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from genlayer_py import create_account, create_client
from genlayer_py.chains import localnet, studionet, testnet_asimov

CHAINS = {"studionet": studionet, "localnet": localnet, "testnet": testnet_asimov}
ROOT = Path(__file__).resolve().parent.parent

# Demo configuration. The source_repo is this repository; swap it for your own
# commit-pinned data repo in production.
SOURCE_REPO = os.environ.get("QUORUM_SOURCE_REPO", "phu1271997/quorum-oracles")

TARGETS = {
    "figure": {
        "path": ROOT / "contracts" / "figure_quorum.py",
        "args": [SOURCE_REPO, "station-kpi-01", "observed daily rainfall total", "length"],
    },
    "claim": {
        "path": ROOT / "contracts" / "claim_quorum.py",
        "args": [SOURCE_REPO, "Does the report confirm the service meets its stated SLA?",
                 ["SUPPORTED", "REFUTED", "UNVERIFIABLE"]],
    },
}


def deploy_one(name: str, client, account, check_only: bool) -> str | None:
    spec = TARGETS[name]
    code = spec["path"].read_text()
    print(f"\n=== {name} ({spec['path'].name}) ===")
    try:
        client.get_contract_schema_for_code(code.encode())
        print("Schema:   OK")
    except Exception as e:  # noqa: BLE001
        print(f"Schema check failed: {e}", file=sys.stderr)
        return None
    if check_only:
        return "check-only"

    tx_hash = client.deploy_contract(code=code, account=account, args=spec["args"])
    print(f"Deploy tx: {tx_hash}")
    receipt = client.wait_for_transaction_receipt(
        transaction_hash=tx_hash, status="FINALIZED", interval=5000, retries=80
    )
    addr = (
        receipt.get("data", {}).get("contract_address")
        if isinstance(receipt, dict)
        else getattr(receipt, "contract_address", None)
    )
    if not addr and isinstance(receipt, dict):
        addr = receipt.get("contract_address") or receipt.get("to")
    print(f"Contract address: {addr}")
    print(f"Explorer: https://explorer-studio.genlayer.com/address/{addr}")
    return addr


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("which", nargs="?", default="both", choices=["figure", "claim", "both"])
    ap.add_argument("--chain", default="studionet", choices=list(CHAINS))
    ap.add_argument("--check-only", action="store_true", help="load schema, do not deploy")
    args = ap.parse_args()

    key = os.environ.get("GENLAYER_PRIVATE_KEY")
    if not args.check_only and (not key or "REPLACE_ME" in key):
        print("ERROR: GENLAYER_PRIVATE_KEY not set. Run: source ~/.genlayer/env.sh", file=sys.stderr)
        return 2

    chain = CHAINS[args.chain]
    account = create_account(key) if key else None
    client = create_client(chain=chain, account=account)
    if account:
        print(f"Deployer: {account.address}")
    print(f"Chain:    {chain.name} (id={chain.id})")

    names = ["figure", "claim"] if args.which == "both" else [args.which]
    results = {}
    for name in names:
        addr = deploy_one(name, client, account, args.check_only)
        if addr is None:
            return 1
        results[name] = addr

    print("\n--- summary ---")
    for name, addr in results.items():
        print(f"{name}: {addr}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
