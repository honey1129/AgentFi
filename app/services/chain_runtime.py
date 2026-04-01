from __future__ import annotations

from web3 import Web3

from app.core.config import get_settings


class ChainRuntimeService:
    @staticmethod
    def inspect_runtime_chain() -> dict:
        settings = get_settings()
        provider_url = settings.web3_provider_url.strip()
        contract_address = settings.nft_contract_address.strip()

        if not provider_url or not contract_address:
            missing = []
            if not provider_url:
                missing.append("WEB3_PROVIDER_URL")
            if not contract_address:
                missing.append("NFT_CONTRACT_ADDRESS")
            return {
                "status": "DISABLED",
                "chain_sync_enabled": False,
                "web3_provider_configured": bool(provider_url),
                "nft_contract_address": contract_address or None,
                "missing": missing,
                "chain_id": None,
                "latest_block": None,
                "contract_code_present": False,
                "error": None,
            }

        try:
            web3 = Web3(Web3.HTTPProvider(provider_url, request_kwargs={"timeout": 3}))
            chain_id = web3.eth.chain_id
            latest_block = web3.eth.block_number
            checksum_contract = Web3.to_checksum_address(contract_address)
            contract_code = web3.eth.get_code(checksum_contract)
        except Exception as exc:
            return {
                "status": "RPC_ERROR",
                "chain_sync_enabled": False,
                "web3_provider_configured": True,
                "nft_contract_address": contract_address,
                "missing": [],
                "chain_id": None,
                "latest_block": None,
                "contract_code_present": False,
                "error": str(exc),
            }

        contract_code_present = bool(contract_code and contract_code != b"\x00" and contract_code != b"")
        return {
            "status": "READY" if contract_code_present else "CONTRACT_MISSING",
            "chain_sync_enabled": contract_code_present,
            "web3_provider_configured": True,
            "nft_contract_address": contract_address,
            "missing": [],
            "chain_id": str(chain_id),
            "latest_block": latest_block,
            "contract_code_present": contract_code_present,
            "error": None if contract_code_present else "Configured NFT contract has no bytecode.",
        }
