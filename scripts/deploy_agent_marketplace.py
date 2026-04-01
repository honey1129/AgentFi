from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from eth_account import Account
from solcx import compile_standard, install_solc, set_solc_version
from web3 import Web3

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.onchain_nft import build_fee_params


CONTRACT_PATH = ROOT / "contracts" / "AgentMarketplace.sol"
DEFAULT_ARTIFACT_PATH = ROOT / "contracts" / "artifacts" / "AgentMarketplace.json"
DEFAULT_SOLC_VERSION = "0.8.24"


def load_env_file(path: str | None) -> None:
    if not path:
        return

    env_path = Path(path)
    if not env_path.is_absolute():
        env_path = ROOT / env_path
    if not env_path.exists():
        raise FileNotFoundError(f"Env file not found: {env_path}")

    for line in env_path.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compile and deploy AgentMarketplace to an EVM chain.")
    parser.add_argument("--env-file", help="Optional env file with DEPLOY_RPC_URL, DEPLOY_PRIVATE_KEY, and NFT_CONTRACT_ADDRESS.")
    parser.add_argument("--rpc-url", help="EVM RPC URL. Defaults to DEPLOY_RPC_URL or WEB3_PROVIDER_URL.")
    parser.add_argument("--private-key", help="Deployer private key. Defaults to DEPLOY_PRIVATE_KEY.")
    parser.add_argument("--nft-contract-address", help="Deployed AgentOwnershipNFT address.")
    parser.add_argument("--solc-version", help=f"Solc version. Defaults to SOLC_VERSION or {DEFAULT_SOLC_VERSION}.")
    parser.add_argument("--artifact-output", default=str(DEFAULT_ARTIFACT_PATH))
    return parser.parse_args()


def require_env_or_arg(cli_value: str | None, *env_keys: str) -> str:
    if cli_value:
        return cli_value
    for key in env_keys:
        value = os.getenv(key)
        if value:
            return value
    joined = ", ".join(env_keys)
    raise ValueError(f"Missing required value. Set one of: {joined}")


def compile_contract(solc_version: str) -> tuple[list[dict], str]:
    install_solc(solc_version)
    set_solc_version(solc_version)

    source = CONTRACT_PATH.read_text()
    compiled = compile_standard(
        {
            "language": "Solidity",
            "sources": {"AgentMarketplace.sol": {"content": source}},
            "settings": {
                "outputSelection": {
                    "*": {
                        "*": ["abi", "evm.bytecode.object"],
                    }
                }
            },
        },
        allow_paths=str(ROOT),
    )

    contract = compiled["contracts"]["AgentMarketplace.sol"]["AgentMarketplace"]
    return contract["abi"], contract["evm"]["bytecode"]["object"]


def write_artifact(path: str, abi: list[dict], bytecode: str, address: str, nft_contract_address: str) -> Path:
    artifact_path = Path(path)
    if not artifact_path.is_absolute():
        artifact_path = ROOT / artifact_path
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(
        json.dumps(
            {
                "contractName": "AgentMarketplace",
                "abi": abi,
                "bytecode": bytecode,
                "address": address,
                "nftContractAddress": nft_contract_address,
            },
            indent=2,
        )
    )
    return artifact_path


def send_transaction(web3: Web3, private_key: str, tx: dict) -> dict:
    signed = Account.sign_transaction(tx, private_key)
    tx_hash = web3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
    if receipt.status != 1:
        raise RuntimeError(f"Transaction reverted: {tx_hash.hex()}")
    return {"tx_hash": tx_hash.hex(), "receipt": receipt}


def main() -> None:
    args = parse_args()
    load_env_file(args.env_file)

    rpc_url = require_env_or_arg(args.rpc_url, "DEPLOY_RPC_URL", "WEB3_PROVIDER_URL")
    private_key = require_env_or_arg(args.private_key, "DEPLOY_PRIVATE_KEY")
    nft_contract_address = Web3.to_checksum_address(
        require_env_or_arg(args.nft_contract_address, "NFT_CONTRACT_ADDRESS")
    )
    solc_version = args.solc_version or os.getenv("SOLC_VERSION", DEFAULT_SOLC_VERSION)

    web3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 5}))
    deployer = Account.from_key(private_key)
    abi, bytecode = compile_contract(solc_version)
    contract = web3.eth.contract(abi=abi, bytecode=bytecode)

    nonce = web3.eth.get_transaction_count(deployer.address)
    deploy_tx = contract.constructor(nft_contract_address).build_transaction(
        {
            "chainId": web3.eth.chain_id,
            "from": deployer.address,
            "nonce": nonce,
            "gas": 4_000_000,
            **build_fee_params(web3),
        }
    )
    deploy_result = send_transaction(web3, private_key, deploy_tx)
    receipt = deploy_result["receipt"]
    deployed_address = receipt.contractAddress

    artifact_path = write_artifact(args.artifact_output, abi, bytecode, deployed_address, nft_contract_address)
    runtime_env = {
        "WEB3_PROVIDER_URL": rpc_url,
        "NFT_CONTRACT_ADDRESS": nft_contract_address,
        "MARKETPLACE_CONTRACT_ADDRESS": deployed_address,
        "PUBLIC_BASE_URL": os.getenv("PUBLIC_BASE_URL", "http://127.0.0.1:8000"),
    }

    print(
        json.dumps(
            {
                "artifact_path": str(artifact_path),
                "chain_id": web3.eth.chain_id,
                "contract_address": deployed_address,
                "deployer": deployer.address,
                "nft_contract_address": nft_contract_address,
                "transactions": [{"action": "deploy", "tx_hash": deploy_result["tx_hash"]}],
                "runtime_env": runtime_env,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
