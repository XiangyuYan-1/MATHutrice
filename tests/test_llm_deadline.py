from types import SimpleNamespace

import pytest

from mathutrice.llm_deadline import DeadlineExceeded, LLMDeadline


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class FakeCompletions:
    def __init__(self, owner, timeout: float, max_retries: int) -> None:
        self.owner = owner
        self.timeout = timeout
        self.max_retries = max_retries

    def create(self, *, model: str, messages: list[dict]):
        self.owner.calls.append(
            {
                "model": model,
                "messages": messages,
                "timeout": self.timeout,
                "max_retries": self.max_retries,
            }
        )
        self.owner.clock.advance(self.owner.call_durations.pop(0))
        content = f"reply-{len(self.owner.calls)}"
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
        )


class BoundFakeClient:
    def __init__(self, owner, timeout: float, max_retries: int) -> None:
        self.chat = SimpleNamespace(
            completions=FakeCompletions(owner, timeout, max_retries)
        )


class FakeClient:
    def __init__(self, clock: FakeClock, call_durations: list[float]) -> None:
        self.clock = clock
        self.call_durations = list(call_durations)
        self.calls: list[dict] = []

    def with_options(self, *, timeout: float, max_retries: int):
        return BoundFakeClient(self, timeout, max_retries)


def test_one_deadline_stops_the_longest_evaluation_at_five_minutes() -> None:
    clock = FakeClock()
    client = FakeClient(clock, call_durations=[120.0, 120.0, 61.0])
    deadline = LLMDeadline(
        client,
        "test-model",
        timeout_seconds=300.0,
        monotonic=clock,
    )
    messages = [{"role": "user", "content": "question"}]

    assert deadline.complete(messages) == "reply-1"
    assert deadline.complete(messages) == "reply-2"

    with pytest.raises(DeadlineExceeded):
        deadline.complete(messages)

    calls_at_deadline = len(client.calls)
    with pytest.raises(DeadlineExceeded):
        deadline.complete(messages)

    assert len(client.calls) == calls_at_deadline == 3
    assert [call["timeout"] for call in client.calls] == pytest.approx(
        [300.0, 180.0, 60.0]
    )
    assert {call["max_retries"] for call in client.calls} == {0}


def test_calls_finishing_inside_the_shared_deadline_complete_normally() -> None:
    clock = FakeClock()
    client = FakeClient(clock, call_durations=[100.0, 100.0])
    deadline = LLMDeadline(
        client,
        "test-model",
        timeout_seconds=300.0,
        monotonic=clock,
    )

    first = deadline.complete([{"role": "user", "content": "first"}])
    second = deadline.complete([{"role": "user", "content": "second"}])

    assert (first, second) == ("reply-1", "reply-2")
    assert [call["timeout"] for call in client.calls] == pytest.approx([300.0, 200.0])
    assert all(call["model"] == "test-model" for call in client.calls)
