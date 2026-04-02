#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${1:-$ROOT_DIR/deploy/local.anvil.env.example}"
ENV_CONTRACT_OWNER="${CONTRACT_OWNER:-}"
ENV_RUNTIME_MINTER_ADDRESS="${RUNTIME_MINTER_ADDRESS:-}"

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
CONTRACT_NAME="${CONTRACT_NAME:-AgentOwnershipNFT}"
CONTRACT_SYMBOL="${CONTRACT_SYMBOL:-AGENT}"
PUBLIC_URL="${PUBLIC_BASE_URL:-http://127.0.0.1:8000}"

DEPLOYER_ADDRESS="$(cast wallet address --private-key "$PRIVATE_KEY")"
CONTRACT_OWNER_ADDRESS="${CONTRACT_OWNER:-$ENV_CONTRACT_OWNER}"
CONTRACT_OWNER_ADDRESS="${CONTRACT_OWNER_ADDRESS:-$DEPLOYER_ADDRESS}"
RUNTIME_MINTER_ADDRESS="${RUNTIME_MINTER_ADDRESS:-$ENV_RUNTIME_MINTER_ADDRESS}"
RUNTIME_MINTER_ADDRESS="${RUNTIME_MINTER_ADDRESS:-$DEPLOYER_ADDRESS}"

DEPLOY_OUTPUT="$(
  cd "$ROOT_DIR" && \
  forge create contracts/AgentOwnershipNFT.sol:AgentOwnershipNFT \
    --rpc-url "$RPC_URL" \
    --private-key "$PRIVATE_KEY" \
    --broadcast \
    --constructor-args "$CONTRACT_NAME" "$CONTRACT_SYMBOL" "$DEPLOYER_ADDRESS"
)"

echo "$DEPLOY_OUTPUT"

CONTRACT_ADDRESS="$(printf '%s\n' "$DEPLOY_OUTPUT" | awk -F': ' '/Deployed to:/ { print $2 }' | tail -n 1)"
DEPLOY_TX_HASH="$(printf '%s\n' "$DEPLOY_OUTPUT" | awk -F': ' '/Transaction hash:/ { print $2 }' | tail -n 1)"

if [[ -z "$CONTRACT_ADDRESS" ]]; then
  echo "Failed to parse deployed contract address from forge output." >&2
  exit 1
fi

SET_MINTER_TX_HASH=""
TRANSFER_OWNER_TX_HASH=""

if [[ "$RUNTIME_MINTER_ADDRESS" != "$DEPLOYER_ADDRESS" ]]; then
  SET_MINTER_OUTPUT="$(cast send "$CONTRACT_ADDRESS" "setMinter(address,bool)" "$RUNTIME_MINTER_ADDRESS" true --rpc-url "$RPC_URL" --private-key "$PRIVATE_KEY")"
  echo "$SET_MINTER_OUTPUT"
  SET_MINTER_TX_HASH="$(printf '%s\n' "$SET_MINTER_OUTPUT" | awk '/transactionHash/ { print $2 }' | tail -n 1)"
fi

if [[ "$CONTRACT_OWNER_ADDRESS" != "$DEPLOYER_ADDRESS" ]]; then
  TRANSFER_OWNER_OUTPUT="$(cast send "$CONTRACT_ADDRESS" "transferOwnership(address)" "$CONTRACT_OWNER_ADDRESS" --rpc-url "$RPC_URL" --private-key "$PRIVATE_KEY")"
  echo "$TRANSFER_OWNER_OUTPUT"
  TRANSFER_OWNER_TX_HASH="$(printf '%s\n' "$TRANSFER_OWNER_OUTPUT" | awk '/transactionHash/ { print $2 }' | tail -n 1)"
fi

cat <<EOF
{
  "chain_id": $(cast chain-id --rpc-url "$RPC_URL"),
  "contract_address": "$CONTRACT_ADDRESS",
  "contract_name": "$CONTRACT_NAME",
  "contract_symbol": "$CONTRACT_SYMBOL",
  "contract_owner": "$CONTRACT_OWNER_ADDRESS",
  "deployer": "$DEPLOYER_ADDRESS",
  "runtime_minter": "$RUNTIME_MINTER_ADDRESS",
  "transactions": {
    "deploy": "$DEPLOY_TX_HASH",
    "set_minter": "$SET_MINTER_TX_HASH",
    "transfer_ownership": "$TRANSFER_OWNER_TX_HASH"
  },
  "runtime_env": {
    "WEB3_PROVIDER_URL": "$RPC_URL",
    "NFT_CONTRACT_ADDRESS": "$CONTRACT_ADDRESS",
    "PUBLIC_BASE_URL": "$PUBLIC_URL",
    "NFT_MINTER_PRIVATE_KEY": "$( [[ "$RUNTIME_MINTER_ADDRESS" == "$DEPLOYER_ADDRESS" ]] && printf '%s' "$PRIVATE_KEY" || printf '%s' '<runtime-minter-private-key>' )"
  }
}
EOF
