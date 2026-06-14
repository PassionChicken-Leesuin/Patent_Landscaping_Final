"""LLM layer: provider-agnostic structured-output client + 10-key loading + Mock.

Primary path uses the OpenAI SDK directly (`chat.completions.parse` with a Pydantic
schema) — robust on Python 3.14 and ideal for multi-key parallelism. Each API key
gets its own client; the runner round-robins patents across them.
"""
from __future__ import annotations
import os
import re
from dataclasses import dataclass, field
from typing import Type

from dotenv import load_dotenv
from pydantic import BaseModel


# ----------------------------------------------------------------- keys
def load_openai_keys(env_path: str | None = None) -> list[str]:
    """Collect OPENAI_API_KEY_1..N (and a bare OPENAI_API_KEY) from .env / environ."""
    load_dotenv(env_path, override=False)
    keys: dict[int, str] = {}
    bare = None
    for name, val in os.environ.items():
        if not val:
            continue
        m = re.fullmatch(r"OPENAI_API_KEY_(\d+)", name)
        if m:
            keys[int(m.group(1))] = val.strip()
        elif name == "OPENAI_API_KEY":
            bare = val.strip()
    ordered = [keys[i] for i in sorted(keys)]
    if not ordered and bare:
        ordered = [bare]
    return ordered


# ----------------------------------------------------------------- usage
@dataclass
class Usage:
    calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0

    def add(self, pt: int, ct: int):
        self.calls += 1
        self.prompt_tokens += pt
        self.completion_tokens += ct

    def merge(self, other: "Usage"):
        self.calls += other.calls
        self.prompt_tokens += other.prompt_tokens
        self.completion_tokens += other.completion_tokens

    # gpt-4o-mini pricing (USD / 1M tokens): in 0.15, out 0.60
    def cost_usd(self, in_rate: float = 0.15, out_rate: float = 0.60) -> float:
        return self.prompt_tokens / 1e6 * in_rate + self.completion_tokens / 1e6 * out_rate


# ----------------------------------------------------------------- clients
class StructuredLLM:
    """Interface: parse(system, user, schema) -> (BaseModel, prompt_tok, completion_tok)."""
    def parse(self, system: str, user: str, schema: Type[BaseModel]):
        raise NotImplementedError


@dataclass
class OpenAIStructuredLLM(StructuredLLM):
    api_key: str
    model: str = "gpt-4o-mini"
    temperature: float = 0.0
    seed: int | None = 7
    _client: object = field(default=None, repr=False)

    def __post_init__(self):
        from openai import OpenAI
        self._client = OpenAI(api_key=self.api_key)

    def parse(self, system: str, user: str, schema: Type[BaseModel]):
        resp = self._client.chat.completions.parse(
            model=self.model,
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user}],
            response_format=schema,
            temperature=self.temperature,
            seed=self.seed,
        )
        msg = resp.choices[0].message
        if getattr(msg, "refusal", None):
            raise RuntimeError(f"model refused: {msg.refusal}")
        u = resp.usage
        return msg.parsed, (u.prompt_tokens if u else 0), (u.completion_tokens if u else 0)


@dataclass
class MockStructuredLLM(StructuredLLM):
    """Offline deterministic stub for smoke tests (no API key needed).

    Crude keyword rules — NOT for real labeling, only to exercise the pipeline.
    """
    model: str = "mock"

    def parse(self, system: str, user: str, schema: Type[BaseModel]):
        from src.mas.schemas import RelevanceOut, ExclusionOut
        t = user.lower()
        auto = any(k in t for k in ("autonomous", "self-driving", "driverless",
                                    "automated driving", "ego vehicle", "motion planning"))
        assist = any(k in t for k in ("driver assist", "warns the driver", "lane departure warning",
                                      "blind spot", "keeps the human", "driver remains"))
        if schema is RelevanceOut:
            if assist and not auto:
                obj = RelevanceOut(core_stance="unrelated", core_score=0.18, route="hard_negative")
            elif auto:
                obj = RelevanceOut(core_stance="related", core_score=0.9, route="easy_positive")
            elif "vehicle" in t or "driving" in t:
                obj = RelevanceOut(core_stance="abstain", core_score=0.55, route="boundary")
            else:
                obj = RelevanceOut(core_stance="unrelated", core_score=0.1, route="easy_negative")
            return obj, 0, 0
        if schema is ExclusionOut:
            if assist:
                obj = ExclusionOut(exclusion_stance="hard_negative", exclusion_risk=0.85,
                                   confusable_category="driver-assistance", exclusion_reason="ADAS")
            else:
                obj = ExclusionOut(exclusion_stance="not_excluded", exclusion_risk=0.2)
            return obj, 0, 0
        raise ValueError(f"MockStructuredLLM: unsupported schema {schema}")
