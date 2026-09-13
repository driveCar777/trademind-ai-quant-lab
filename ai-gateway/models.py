"""Pydantic request/response models for AI Gateway V3.0.

These schemas match the API contract defined in V3_AI_GATEWAY_SPEC.md.
All three content endpoints (generate / describe / signal) share the same
request shape (type + context + params); chat uses a messages list.
"""

from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str
    content: str


class GenerateRequest(BaseModel):
    """投研报告 / 策略描述 / 信号解读 通用请求。"""

    type: str = Field(
        ...,
        description="research_report | strategy_description | signal_interpretation",
    )
    context: Dict[str, Any] = Field(default_factory=dict)
    params: Dict[str, Any] = Field(default_factory=dict)
    model: str = ""


class DescribeRequest(BaseModel):
    """策略自然语言描述请求（与 GenerateRequest 同构）。"""

    type: str = "strategy_description"
    context: Dict[str, Any] = Field(default_factory=dict)
    params: Dict[str, Any] = Field(default_factory=dict)
    model: str = ""


class SignalRequest(BaseModel):
    """信号解读请求（与 GenerateRequest 同构）。"""

    type: str = "signal_interpretation"
    context: Dict[str, Any] = Field(default_factory=dict)
    params: Dict[str, Any] = Field(default_factory=dict)
    model: str = ""


class ChatRequest(BaseModel):
    """通用对话请求（调试用）。"""

    messages: List[ChatMessage] = Field(..., min_length=1)
    params: Dict[str, Any] = Field(default_factory=dict)
    model: str = ""
