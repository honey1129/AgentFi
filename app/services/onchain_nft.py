from __future__ import annotations

from dataclasses import dataclass

from eth_account import Account
from web3 import Web3

from app.core.config import get_settings
from app.services.token_metadata import build_token_metadata_uri


AGENT_OWNERSHIP_NFT_ABI = [
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "from", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "to", "type": "address"},
            {"indexed": True, "internalType": "uint256", "name": "tokenId", "type": "uint256"},
        ],
        "name": "Transfer",
        "type": "event",
    },
    {
        "inputs": [
            {"internalType": "address", "name": "to", "type": "address"},
            {"internalType": "string", "name": "uri", "type": "string"},
        ],
        "name": "mintTo",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "address", "name": "account", "type": "address"}],
        "name": "minters",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function",
    },
]


class OnchainMintError(RuntimeError):
    pass


@dataclass(frozen=True)
class MintedOwnershipNFT:
    block_number: int
    chain_token_id: str
    contract_address: str
    metadata_uri: str
    tx_hash: str


def build_fee_params(web3: Web3) -> dict:
    latest_block = web3.eth.get_block("latest")
    base_fee = latest_block.get("baseFeePerGas")
    if base_fee is not None:
        try:
            priority_fee = web3.eth.max_priority_fee
        except Exception:
            priority_fee = web3.to_wei(2, "gwei")
        return {
            "maxFeePerGas": int(base_fee) + int(priority_fee) * 2,
            "maxPriorityFeePerGas": int(priority_fee),
        }
    return {"gasPrice": web3.eth.gas_price}


def build_metadata_uri(runtime_token_id: str) -> str:
    return build_token_metadata_uri(runtime_token_id)


def is_runtime_mint_ready(contract_address: str | None) -> bool:
    settings = get_settings()
    return bool(settings.web3_provider_url and settings.nft_minter_private_key and contract_address)


def mint_agent_ownership_nft(
    *,
    contract_address: str,
    owner_chain_address: str,
    runtime_token_id: str,
) -> MintedOwnershipNFT:
    settings = get_settings()
    if not settings.web3_provider_url:
        raise OnchainMintError("WEB3_PROVIDER_URL is not configured.")
    if not settings.nft_minter_private_key:
        raise OnchainMintError("NFT_MINTER_PRIVATE_KEY is not configured.")
    if not Web3.is_address(contract_address):
        raise OnchainMintError("Invalid NFT contract address.")
    if not Web3.is_address(owner_chain_address):
        raise OnchainMintError("Invalid owner chain address.")

    web3 = Web3(Web3.HTTPProvider(settings.web3_provider_url, request_kwargs={"timeout": 5}))
    minter_account = Account.from_key(settings.nft_minter_private_key)
    contract = web3.eth.contract(
        address=Web3.to_checksum_address(contract_address),
        abi=AGENT_OWNERSHIP_NFT_ABI,
    )

    metadata_uri = build_metadata_uri(runtime_token_id)
    recipient = Web3.to_checksum_address(owner_chain_address)
    nonce = web3.eth.get_transaction_count(minter_account.address)
    mint_call = contract.functions.mintTo(recipient, metadata_uri)

    tx = mint_call.build_transaction(
        {
            "chainId": web3.eth.chain_id,
            "from": minter_account.address,
            "nonce": nonce,
            **build_fee_params(web3),
        }
    )
    try:
        tx["gas"] = int(mint_call.estimate_gas({"from": minter_account.address}) * 1.2)
    except Exception:
        tx["gas"] = 500_000

    signed_tx = Account.sign_transaction(tx, settings.nft_minter_private_key)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
    receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=settings.nft_tx_timeout_seconds)
    if receipt.status != 1:
        raise OnchainMintError("Mint transaction reverted.")

    transfer_logs = contract.events.Transfer().process_receipt(receipt)
    minted_log = next((log for log in transfer_logs if log["args"]["from"] == "0x0000000000000000000000000000000000000000"), None)
    if minted_log is None:
        raise OnchainMintError("Mint receipt did not contain a Transfer-from-zero log.")

    return MintedOwnershipNFT(
        block_number=int(receipt.blockNumber),
        chain_token_id=str(minted_log["args"]["tokenId"]),
        contract_address=contract_address.lower(),
        metadata_uri=metadata_uri,
        tx_hash=tx_hash.hex(),
    )
