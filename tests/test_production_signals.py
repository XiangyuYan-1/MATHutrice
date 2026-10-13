from types import SimpleNamespace

import pytest

from mathutrice import app
from mathutrice.fonctions_python import chatbot


POSTHOG_SETTINGS = (
    "POSTHOG_PROJECT_TOKEN",
    "POSTHOG_HOST",
    "POSTHOG_ENVIRONMENT",
)


def _set_posthog(monkeypatch, **settings):
    for name in POSTHOG_SETTINGS:
        monkeypatch.setenv(name, settings.get(name, ""))


def test_production_signals_are_off_when_every_setting_is_unset(monkeypatch):
    _set_posthog(monkeypatch)

    assert app.start_production_signals() == (None, None, None)


@pytest.mark.parametrize(
    ("settings", "missing"),
    [
        ({"POSTHOG_PROJECT_TOKEN": "phc_test"}, "POSTHOG_HOST missing"),
        ({"POSTHOG_HOST": "https://eu.i.posthog.com"}, "POSTHOG_PROJECT_TOKEN missing"),
        ({"POSTHOG_ENVIRONMENT": "test"}, "POSTHOG_PROJECT_TOKEN missing"),
    ],
)
def test_partial_production_signal_settings_refuse_to_start(
    monkeypatch, settings, missing
):
    _set_posthog(monkeypatch, **settings)

    with pytest.raises(ValueError, match=f"^{missing}$"):
        app.start_production_signals()


def test_a_caught_chat_failure_is_reported_before_the_answer(monkeypatch):
    failure = RuntimeError("provider failed")

    class FailingCompletions:
        def create(self, **kwargs):
            raise failure

    fake_client = SimpleNamespace(
        chat=SimpleNamespace(completions=FailingCompletions())
    )
    monkeypatch.setattr(chatbot, "client", fake_client)
    reported = []

    answer = "".join(
        chatbot.chat_stream_with_history(
            [{"role": "user", "content": "bonjour"}],
            report_failure=reported.append,
        )
    )

    assert answer == "Erreur: provider failed"
    assert reported == [failure]
