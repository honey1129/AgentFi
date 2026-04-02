from __future__ import annotations

from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware


def build_web3(rpc_url: str, *, timeout: int = 5) -> Web3:
    web3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": timeout}))
    web3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    return web3
