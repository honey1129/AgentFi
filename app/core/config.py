from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import os


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "AgentFi Runtime")
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))
    api_prefix: str = os.getenv("API_PREFIX", "/v1")
    mysql_host: str = os.getenv("MYSQL_HOST", "127.0.0.1")
    mysql_port: int = int(os.getenv("MYSQL_PORT", "3306"))
    mysql_database: str = os.getenv("MYSQL_DATABASE", "agentfi")
    mysql_user: str = os.getenv("MYSQL_USER", "agentfi")
    mysql_password: str = os.getenv("MYSQL_PASSWORD", "agentfi")
    redis_url: str = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")
    celery_broker_url: str = os.getenv("CELERY_BROKER_URL", os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0"))
    celery_result_backend: str = os.getenv("CELERY_RESULT_BACKEND", os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0"))
    scheduler_tick_seconds: int = int(os.getenv("SCHEDULER_TICK_SECONDS", "10"))
    executor_mode: str = os.getenv("AGENT_EXECUTOR_MODE", "mock")
    model_base_url: str = os.getenv("MODEL_BASE_URL", os.getenv("LLM_BASE_URL", "")).rstrip("/")
    model_api_key: str = os.getenv("MODEL_API_KEY", os.getenv("LLM_API_KEY", ""))
    model_name: str = os.getenv("MODEL_NAME", os.getenv("LLM_MODEL", ""))
    public_base_url: str = os.getenv("PUBLIC_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
    web3_provider_url: str = os.getenv("WEB3_PROVIDER_URL", "")
    nft_contract_address: str = os.getenv("NFT_CONTRACT_ADDRESS", "").lower()
    marketplace_contract_address: str = os.getenv("MARKETPLACE_CONTRACT_ADDRESS", "").lower()
    nft_minter_private_key: str = os.getenv("NFT_MINTER_PRIVATE_KEY", "")
    web3_start_block: str = os.getenv("WEB3_START_BLOCK", "")
    web3_poll_interval_seconds: int = int(os.getenv("WEB3_POLL_INTERVAL_SECONDS", "5"))
    web3_block_batch_size: int = int(os.getenv("WEB3_BLOCK_BATCH_SIZE", "1000"))
    nft_tx_timeout_seconds: int = int(os.getenv("NFT_TX_TIMEOUT_SECONDS", "120"))
    redis_lock_ttl_seconds: int = int(os.getenv("REDIS_LOCK_TTL_SECONDS", "30"))
    owner_cache_ttl_seconds: int = int(os.getenv("OWNER_CACHE_TTL_SECONDS", "3600"))
    wallet_auth_challenge_ttl_seconds: int = int(os.getenv("WALLET_AUTH_CHALLENGE_TTL_SECONDS", "300"))
    wallet_auth_session_ttl_seconds: int = int(os.getenv("WALLET_AUTH_SESSION_TTL_SECONDS", "43200"))
    auth_rate_limit_window_seconds: int = int(os.getenv("AUTH_RATE_LIMIT_WINDOW_SECONDS", "60"))
    auth_challenge_rate_limit: int = int(os.getenv("AUTH_CHALLENGE_RATE_LIMIT", "8"))
    auth_verify_rate_limit: int = int(os.getenv("AUTH_VERIFY_RATE_LIMIT", "8"))
    mutation_rate_limit_window_seconds: int = int(os.getenv("MUTATION_RATE_LIMIT_WINDOW_SECONDS", "60"))
    mutation_rate_limit_per_wallet: int = int(os.getenv("MUTATION_RATE_LIMIT_PER_WALLET", "30"))
    run_default_timeout_seconds: int = int(os.getenv("RUN_DEFAULT_TIMEOUT_SECONDS", "90"))
    run_default_max_attempts: int = int(os.getenv("RUN_DEFAULT_MAX_ATTEMPTS", "3"))
    run_retry_backoff_seconds: int = int(os.getenv("RUN_RETRY_BACKOFF_SECONDS", "5"))
    runtime_log_default_limit: int = int(os.getenv("RUNTIME_LOG_DEFAULT_LIMIT", "50"))

    @property
    def database_url(self) -> str:
        return (
            f"mysql+aiomysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
