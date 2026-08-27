"""Retry prompt generation for failed LLM validation."""

from __future__ import annotations

MAX_RETRIES = 2


def build_retry_prompt(errors: list) -> str:
    """Build a retry prompt from validation error list."""
    error_lines = "\n".join(f"- {e}" for e in errors)
    return (
        "上一次输出未通过程序校验，请严格修正以下问题，并重新输出完整 JSON。\n\n"
        "错误列表：\n"
        f"{error_lines}\n\n"
        "要求：\n"
        "- 只输出合法 JSON\n"
        "- 不要输出解释\n"
        "- 不要输出 Markdown\n"
        "- 所有时间必须为 HH:MM:SS.mmm\n"
    )


def should_retry(result, retry_count: int) -> bool:
    """Check if we should retry based on validation result and retry count."""
    return (not result.valid) and retry_count < MAX_RETRIES
