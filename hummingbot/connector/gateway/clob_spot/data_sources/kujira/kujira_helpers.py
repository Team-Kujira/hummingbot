import hashlib
from datetime import datetime
from typing import Any, List

import jsonpickle


def generate_hash(input: Any) -> str:
    return generate_hashes([input])[0]


def generate_hashes(inputs: List[Any]) -> List[str]:
    hashes = []
    salt = datetime.now()

    for input in inputs:
        serialized = jsonpickle.encode(input, unpicklable=True)
        hasher = hashlib.md5()
        target = f"{salt}{serialized}".encode("utf-8")
        hasher.update(target)
        hash = hasher.hexdigest()

        hashes.append(hash)

    return hashes


def convert_hb_trading_pair_to_market_name(trading_pair: str) -> str:
    return trading_pair.replace("-", "/")


def convert_market_name_to_hb_trading_pair(market_name: str) -> str:
    return market_name.replace("/", "-")
