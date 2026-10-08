"""Versioned named streams, with no ambient seed or process-dependent hash()."""

import hashlib
import json
from random import Random


RNG_SCHEME = "sha256-json-name-mt19937-v1"


class NamedRandomness:
    """Own persistent streams for one run.

    Stream identity is its exact, case-sensitive name. Distinct stream draws do
    not interfere, but extra draws within one stream shift its remaining values.
    Replay requires unchanged draw methods/order and CPython 3.12.13. Callers must
    not reseed streams or replace their state; restore is not implemented here.
    """

    scheme = RNG_SCHEME

    def __init__(self, root_seed: int) -> None:
        if type(root_seed) is not int:
            raise TypeError("root seed must be an integer (not bool)")
        self._root_seed = root_seed
        self._streams: dict[str, Random] = {}

    @property
    def root_seed(self) -> int:
        return self._root_seed

    def stream(self, name: str) -> Random:
        if not isinstance(name, str):
            raise TypeError("stream name must be a string")
        if not name.strip():
            raise ValueError("stream name must be nonempty")
        if name not in self._streams:
            material = json.dumps([RNG_SCHEME, self._root_seed, name],
                                  ensure_ascii=True, separators=(",", ":")).encode("utf-8")
            seed = int.from_bytes(hashlib.sha256(material).digest(), "big")
            self._streams[name] = Random(seed)
        return self._streams[name]
