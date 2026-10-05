"""Install a minimal `genlayer` stub so the deterministic helpers in the
contract modules can be imported and tested off-chain.

Only the names touched at import time and by the pure-Python helpers are
provided. The non-deterministic paths (web.get / exec_prompt / run_nondet) are
exercised on chain, not here.
"""
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class _UserError(Exception):
    pass


class _Return:
    def __init__(self, calldata):
        self.calldata = calldata


class _Generic:
    """Stands in for TreeMap[...] / DynArray[...] annotations."""

    def __class_getitem__(cls, item):
        return cls


class _TreeMap(_Generic):
    pass


class _DynArray(_Generic):
    pass


def _identity_decorator(fn):
    return fn


class _Public:
    write = staticmethod(_identity_decorator)
    view = staticmethod(_identity_decorator)


class _Vm:
    UserError = _UserError
    Return = _Return

    @staticmethod
    def run_nondet_unsafe(leader, validator):  # pragma: no cover - not used off chain
        raise RuntimeError("non-deterministic path is on-chain only")


class _Nondet:
    class web:
        @staticmethod
        def get(url):  # pragma: no cover
            raise RuntimeError("web access is on-chain only")

    @staticmethod
    def exec_prompt(*a, **k):  # pragma: no cover
        raise RuntimeError("LLM access is on-chain only")


class _Gl:
    public = _Public
    vm = _Vm
    nondet = _Nondet

    class Contract:
        pass


genlayer = types.ModuleType("genlayer")
genlayer.gl = _Gl
genlayer.TreeMap = _TreeMap
genlayer.DynArray = _DynArray
genlayer.Address = str
genlayer.bigint = int


def _allow_storage(cls):
    return cls


genlayer.allow_storage = _allow_storage
# `from genlayer import *` pulls these names.
genlayer.__all__ = ["gl", "TreeMap", "DynArray", "Address", "bigint", "allow_storage"]

sys.modules["genlayer"] = genlayer
