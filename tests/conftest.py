import os
from unittest.mock import patch


# Project modules may load dotenv and construct the shared LLM client at import
# time.  Disable dotenv before pytest imports a test module and provide inert
# values so the unit suite never depends on a developer's .env file.
_load_dotenv_patcher = patch("dotenv.load_dotenv", return_value=False)
_load_dotenv_patcher.start()

os.environ.setdefault("LLM_BASE_URL", "https://llm.invalid/v1")
os.environ.setdefault("LLM_API_KEY", "test-only-key")
os.environ.setdefault("LLM_MODEL", "test-only-model")


def pytest_sessionfinish() -> None:
    _load_dotenv_patcher.stop()
