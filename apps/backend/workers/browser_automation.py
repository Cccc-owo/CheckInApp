from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping


DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
)


def _mapping_get(item: Any, key: str, default: Any = None) -> Any:
    if isinstance(item, Mapping):
        return item.get(key, default)
    return getattr(item, key, default)


@dataclass(frozen=True)
class PlaywrightLaunchConfig:
    executable_path: str = ""
    headless: bool = True
    args: tuple[str, ...] = field(
        default_factory=lambda: ("--no-sandbox", "--disable-dev-shm-usage")
    )
    user_agent: str = DEFAULT_USER_AGENT
    viewport_width: int = 1920
    viewport_height: int = 1080
    ignore_https_errors: bool = True

    def to_launch_kwargs(self) -> dict[str, Any]:
        kwargs: dict[str, Any] = {
            "headless": self.headless,
            "args": list(self.args),
        }
        if self.executable_path:
            kwargs["executable_path"] = self.executable_path
        return kwargs

    def to_context_kwargs(self) -> dict[str, Any]:
        return {
            "user_agent": self.user_agent,
            "viewport": {"width": self.viewport_width, "height": self.viewport_height},
            "ignore_https_errors": self.ignore_https_errors,
        }


def extract_cookie_value(cookies: Iterable[Any], cookie_name: str) -> str | None:
    for cookie in cookies:
        if _mapping_get(cookie, "name") == cookie_name:
            value = _mapping_get(cookie, "value")
            if isinstance(value, str) and value.strip():
                return value
    return None


def extract_payload_header(headers: Mapping[str, Any]) -> str | None:
    for key, value in headers.items():
        if key.lower() == "x-api-request-payload" and isinstance(value, str):
            stripped = value.strip()
            if stripped:
                return stripped
    return None


def save_page_debug_artifacts(page: Any, screenshot_path: Path, html_path: Path) -> None:
    screenshot_path.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(screenshot_path))
    html_path.write_text(page.content(), encoding="utf-8")
