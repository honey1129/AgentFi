#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${1:-$ROOT_DIR/deploy/local.anvil.env.example}"
ENV_NFT_CONTRACT_ADDRESS="${NFT_CONTRACT_ADDRESS:-}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Env file not found: $ENV_FILE" >&2
  exit 1
fi

if ! command -v forge >/dev/null 2>&1; then
  echo "forge is required for local deployment." >&2
  exit 1
fi

if ! command -v cast >/dev/null 2>&1; then
  echo "cast is required for local deployment." >&2
  exit 1
fi

set -a
source "$ENV_FILE"
set +a

RPC_URL="${DEPLOY_RPC_URL:-http://127.0.0.1:8545}"
RPC_URL="${RPC_URL/host.docker.internal/127.0.0.1}"
PRIVATE_KEY="${DEPLOY_PRIVATE_KEY:?DEPLOY_PRIVATE_KEY is required}"
NFT_CONTRACT_ADDRESS="${NFT_CONTRACT_ADDRESS:-$ENV_NFT_CONTRACT_ADDRESS}"
NFT_CONTRACT_ADDRESS="${NFT_CONTRACT_ADDRESS:?NFT_CONTRACT_ADDRESS is required}"

DEPLOYER_ADDRESS="$(cast wallet address --private-key "$PRIVATE_KEY")"

DEPLOY_OUTPUT="$(
  cd "$ROOT_DIR" && \
  forge create contracts/AgentMarketplace.sol:AgentMarketplace \
    --rpc-url "$RPC_URL" \
    --private-key "$PRIVATE_KEY" \
    --broadcast \
    --constructor-args "$NFT_CONTRACT_ADDRESS"
)"

echo "$DEPLOY_OUTPUT"

CONTRACT_ADDRESS="$(printf '%s\n' "$DEPLOY_OUTPUT" | awk -F': ' '/Deployed to:/ { print $2 }' | tail -n 1)"
DEPLOY_TX_HASH="$(printf '%s\n' "$DEPLOY_OUTPUT" | awk -F': ' '/Transaction hash:/ { print $2 }' | tail -n 1)"

if [[ -z "$CONTRACT_ADDRESS" ]]; then
  echo "Failed to parse deployed contract address from forge output." >&2
  exit 1
fi

cat <<EOF
{
  "chain_id": $(cast chain-id --rpc-url "$RPC_URL"),
  "contract_address": "$CONTRACT_ADDRESS",
  "deployer": "$DEPLOYER_ADDRESS",
  "nft_contract_address": "$NFT_CONTRACT_ADDRESS",
  "transactions": {
    "deploy": "$DEPLOY_TX_HASH"
  },
  "runtime_env": {
    "WEB3_PROVIDER_URL": "http://host.docker.internal:8545",
    "NFT_CONTRACT_ADDRESS": "$NFT_CONTRACT_ADDRESS",
    "MARKETPLACE_CONTRACT_ADDRESS": "$CONTRACT_ADDRESS"
  }
}
EOF
