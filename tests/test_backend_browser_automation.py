from __future__ import annotations

from backend.workers.browser_automation import (
    PlaywrightLaunchConfig,
    extract_cookie_value,
    extract_payload_header,
)


def test_payload_header_extraction_is_case_insensitive() -> None:
    headers = {
        "Accept": "application/json",
        "X-API-Request-Payload": "live-signature",
    }

    assert extract_payload_header(headers) == "live-signature"


def test_payload_header_extraction_ignores_blank_values() -> None:
    headers = {"x-api-request-payload": "   "}

    assert extract_payload_header(headers) is None


def test_cookie_value_extraction_finds_named_cookie() -> None:
    cookies = [
        {"name": "other", "value": "unused"},
        {"name": "token", "value": "qq-token"},
    ]

    assert extract_cookie_value(cookies, "token") == "qq-token"


def test_launch_config_uses_optional_executable_path() -> None:
    config = PlaywrightLaunchConfig(executable_path="/usr/bin/chromium")

    assert config.to_launch_kwargs()["executable_path"] == "/usr/bin/chromium"
