"""One shared deadline for a sequence of LLM completion calls."""

from collections.abc import Callable
import time
from typing import Any

from openai import APITimeoutError


class DeadlineExceeded(TimeoutError):
    """Raised when an evaluation has exhausted its LLM time budget."""


class LLMDeadline:
    """Apply one time budget to every completion made for an evaluation."""

    def __init__(
        self,
        client: Any,
        model: str,
        *,
        timeout_seconds: float = 300.0,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be greater than zero")

        self._client = client
        self._model = model
        self._monotonic = monotonic
        self._deadline = monotonic() + timeout_seconds
        self._expired = False

    def complete(self, messages: list[dict]) -> str:
        """Return one completion without extending the evaluation deadline."""
        remaining = self._deadline - self._monotonic()
        if self._expired or remaining <= 0:
            self._expired = True
            raise DeadlineExceeded("The evaluation LLM deadline was exceeded")

        try:
            response = (
                self._client.with_options(timeout=300.0, max_retries=0)
                .chat.completions.create(model=self._model, messages=messages)
            )
        except (APITimeoutError, TimeoutError) as exc:
            self._expired = True
            raise DeadlineExceeded(
                "The evaluation LLM deadline was exceeded"
            ) from exc

        if self._monotonic() >= self._deadline:
            self._expired = True
            raise DeadlineExceeded("The evaluation LLM deadline was exceeded")

        return response.choices[0].message.content
