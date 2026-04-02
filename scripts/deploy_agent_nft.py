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
from app.services.web3_client import build_web3


CONTRACT_PATH = ROOT / "contracts" / "AgentOwnershipNFT.sol"
DEFAULT_ARTIFACT_PATH = ROOT / "contracts" / "artifacts" / "AgentOwnershipNFT.json"
DEFAULT_SOLC_VERSION = "0.8.28"


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
    parser = argparse.ArgumentParser(description="Compile and deploy AgentOwnershipNFT to an EVM chain.")
    parser.add_argument("--env-file", help="Optional env file with DEPLOY_RPC_URL and DEPLOY_PRIVATE_KEY.")
    parser.add_argument("--rpc-url", help="EVM RPC URL. Defaults to DEPLOY_RPC_URL or WEB3_PROVIDER_URL.")
    parser.add_argument("--private-key", help="Deployer private key. Defaults to DEPLOY_PRIVATE_KEY.")
    parser.add_argument("--name", help="Contract name. Defaults to CONTRACT_NAME or AgentOwnershipNFT.")
    parser.add_argument("--symbol", help="Contract symbol. Defaults to CONTRACT_SYMBOL or AGENT.")
    parser.add_argument("--contract-owner", help="Final contract owner address. Defaults to deployer.")
    parser.add_argument("--runtime-minter", help="Runtime minter address to authorize after deploy.")
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
            "sources": {"AgentOwnershipNFT.sol": {"content": source}},
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

    contract = compiled["contracts"]["AgentOwnershipNFT.sol"]["AgentOwnershipNFT"]
    return contract["abi"], contract["evm"]["bytecode"]["object"]


def write_artifact(path: str, abi: list[dict], bytecode: str, address: str) -> Path:
    artifact_path = Path(path)
    if not artifact_path.is_absolute():
        artifact_path = ROOT / artifact_path
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(
        json.dumps(
            {
                "contractName": "AgentOwnershipNFT",
                "abi": abi,
                "bytecode": bytecode,
                "address": address,
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
    contract_name = args.name or os.getenv("CONTRACT_NAME", "AgentOwnershipNFT")
    contract_symbol = args.symbol or os.getenv("CONTRACT_SYMBOL", "AGENT")
    solc_version = args.solc_version or os.getenv("SOLC_VERSION", DEFAULT_SOLC_VERSION)
    contract_owner_raw = args.contract_owner or os.getenv("CONTRACT_OWNER")
    runtime_minter_raw = args.runtime_minter or os.getenv("RUNTIME_MINTER_ADDRESS")

    web3 = build_web3(rpc_url, timeout=5)
    deployer = Account.from_key(private_key)
    contract_owner = Web3.to_checksum_address(contract_owner_raw) if contract_owner_raw else deployer.address
    runtime_minter = Web3.to_checksum_address(runtime_minter_raw) if runtime_minter_raw else None

    abi, bytecode = compile_contract(solc_version)
    contract = web3.eth.contract(abi=abi, bytecode=bytecode)

    nonce = web3.eth.get_transaction_count(deployer.address)
    deploy_tx = contract.constructor(contract_name, contract_symbol, deployer.address).build_transaction(
        {
            "chainId": web3.eth.chain_id,
            "from": deployer.address,
            "nonce": nonce,
            "gas": 5_000_000,
            **build_fee_params(web3),
        }
    )
    deploy_result = send_transaction(web3, private_key, deploy_tx)
    receipt = deploy_result["receipt"]
    deployed_address = receipt.contractAddress
    deployed_contract = web3.eth.contract(address=deployed_address, abi=abi)

    transactions = [{"action": "deploy", "tx_hash": deploy_result["tx_hash"]}]
    nonce += 1

    if runtime_minter and runtime_minter != deployer.address:
        set_minter_tx = deployed_contract.functions.setMinter(runtime_minter, True).build_transaction(
            {
                "chainId": web3.eth.chain_id,
                "from": deployer.address,
                "nonce": nonce,
                "gas": 200_000,
                **build_fee_params(web3),
            }
        )
        set_minter_result = send_transaction(web3, private_key, set_minter_tx)
        transactions.append({"action": "set_minter", "tx_hash": set_minter_result["tx_hash"], "account": runtime_minter})
        nonce += 1

    if contract_owner != deployer.address:
        transfer_owner_tx = deployed_contract.functions.transferOwnership(contract_owner).build_transaction(
            {
                "chainId": web3.eth.chain_id,
                "from": deployer.address,
                "nonce": nonce,
                "gas": 150_000,
                **build_fee_params(web3),
            }
        )
        transfer_owner_result = send_transaction(web3, private_key, transfer_owner_tx)
        transactions.append(
            {
                "action": "transfer_ownership",
                "tx_hash": transfer_owner_result["tx_hash"],
                "owner": contract_owner,
            }
        )

    artifact_path = write_artifact(args.artifact_output, abi, bytecode, deployed_address)

    runtime_env = {
        "WEB3_PROVIDER_URL": rpc_url,
        "NFT_CONTRACT_ADDRESS": deployed_address,
        "PUBLIC_BASE_URL": os.getenv("PUBLIC_BASE_URL", "http://127.0.0.1:8000"),
        "NFT_MINTER_PRIVATE_KEY": private_key if runtime_minter in (None, deployer.address) else "<private-key-for-runtime-minter>",
    }

    print(
        json.dumps(
            {
                "artifact_path": str(artifact_path),
                "chain_id": web3.eth.chain_id,
                "contract_address": deployed_address,
                "contract_name": contract_name,
                "contract_symbol": contract_symbol,
                "contract_owner": contract_owner,
                "deployer": deployer.address,
                "runtime_minter": runtime_minter or deployer.address,
                "transactions": transactions,
                "runtime_env": runtime_env,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
