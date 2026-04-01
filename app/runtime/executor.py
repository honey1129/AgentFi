from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
import re
from typing import Any

import httpx

from app.core.config import Settings, get_settings
from app.core.utils import clamp_text
from app.db.models import Agent, AgentNFT, Wallet


class RuntimeExecutionError(RuntimeError):
    pass


class BaseAgentExecutor(ABC):
    @abstractmethod
    async def execute(
        self,
        *,
        agent: Agent,
        nft: AgentNFT,
        owner: Wallet,
        task: str,
    ) -> dict[str, Any]:
        raise NotImplementedError


class MockAgentExecutor(BaseAgentExecutor):
    async def execute(
        self,
        *,
        agent: Agent,
        nft: AgentNFT,
        owner: Wallet,
        task: str,
    ) -> dict[str, Any]:
        forced_sleep_seconds = _parse_mock_sleep_seconds(task)
        if forced_sleep_seconds:
            await asyncio.sleep(forced_sleep_seconds)

        lowered = task.lower()
        if "[mock:fail]" in lowered or "mock fail" in lowered:
            raise RuntimeExecutionError("Mock executor forced a failure for this run.")

        recent_memory = agent.memory_json[-3:] if agent.memory_json else []
        recent_inputs = [entry.get("task", "") for entry in recent_memory if entry.get("task")]
        actions = _derive_actions(task)
        return {
            "provider": "mock",
            "answer": (
                f"{agent.name} 已接受任务：{task}。"
                f" 当前控制权绑定在 NFT {nft.token_id}，持有人钱包为 {owner.id}。"
                f" Agent 将遵循系统目标：{clamp_text(agent.system_prompt, 160)}"
            ),
            "plan": [
                "验证 NFT 所有权",
                "读取最近运行记忆",
                "基于 agent 目标生成可执行动作",
            ],
            "actions": actions,
            "memory_signals": recent_inputs,
            "ownership": {
                "token_id": nft.token_id,
                "owner_wallet_id": owner.id,
            },
        }


class OpenAICompatibleExecutor(BaseAgentExecutor):
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def execute(
        self,
        *,
        agent: Agent,
        nft: AgentNFT,
        owner: Wallet,
        task: str,
    ) -> dict[str, Any]:
        if not self.settings.model_base_url or not self.settings.model_api_key or not self.settings.model_name:
            raise RuntimeExecutionError("OpenAI-compatible executor is enabled but LLM config is incomplete.")

        system_content = (
            f"You are an on-host agent named {agent.name}. "
            f"The owner of the agent is represented by NFT {nft.token_id} and wallet {owner.id}. "
            f"Obey the system goal below and answer in concise JSON-compatible prose.\n\n"
            f"System goal:\n{agent.system_prompt}"
        )
        user_content = (
            f"Task: {task}\n\n"
            f"Agent description: {agent.description}\n"
            f"Recent memory: {agent.memory_json[-5:] if agent.memory_json else []}"
        )

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.settings.model_base_url}/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.settings.model_api_key}"},
                json={
                    "model": self.settings.model_name,
                    "messages": [
                        {"role": "system", "content": system_content},
                        {"role": "user", "content": user_content},
                    ],
                    "temperature": 0.2,
                },
            )
            response.raise_for_status()
            payload = response.json()

        try:
            content = payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:
            raise RuntimeExecutionError("Unexpected LLM response shape.") from exc

        return {
            "provider": "openai_compatible",
            "answer": content,
            "plan": ["ownership-checked", "prompt-loaded", "llm-generated"],
            "actions": _derive_actions(task),
            "ownership": {"token_id": nft.token_id, "owner_wallet_id": owner.id},
        }


def build_executor() -> BaseAgentExecutor:
    settings = get_settings()
    if settings.executor_mode == "openai_compatible":
        return OpenAICompatibleExecutor(settings)
    return MockAgentExecutor()


def _derive_actions(task: str) -> list[str]:
    lowered = task.lower()
    actions: list[str] = []
    if "price" in lowered or "sell" in lowered or "trade" in lowered:
        actions.append("评估是否需要挂牌或调整出售策略")
    if "research" in lowered or "analyze" in lowered:
        actions.append("整理输入上下文并输出分析结论")
    if "build" in lowered or "implement" in lowered:
        actions.append("拆解交付步骤并生成执行方案")
    if not actions:
        actions.append("围绕当前任务生成一轮 owner-scoped 响应")
    return actions


def _parse_mock_sleep_seconds(task: str) -> int:
    match = re.search(r"\[mock:sleep=(\d+)\]", task.lower())
    if match is None:
        return 0
    try:
        return max(int(match.group(1)), 0)
    except ValueError:
        return 0
