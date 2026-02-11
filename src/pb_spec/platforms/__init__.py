"""Platform registry and factory functions."""

from pb_spec.platforms.base import Platform
from pb_spec.platforms.claude import ClaudePlatform
from pb_spec.platforms.copilot import CopilotPlatform
from pb_spec.platforms.opencode import OpenCodePlatform

ALL_PLATFORM_NAMES = ["claude", "copilot", "opencode"]

_REGISTRY: dict[str, type[Platform]] = {
    "claude": ClaudePlatform,
    "copilot": CopilotPlatform,
    "opencode": OpenCodePlatform,
}


def get_platform(name: str) -> Platform:
    """Get platform instance by name."""
    cls = _REGISTRY.get(name)
    if cls is None:
        raise ValueError(
            f"Unknown platform: {name!r}. Choose from: {', '.join(ALL_PLATFORM_NAMES)}"
        )
    return cls()


def resolve_targets(ai: str) -> list[str]:
    """Resolve --ai argument to list of platform names.

    'all' -> ['claude', 'copilot', 'opencode']
    """
    if ai == "all":
        return list(ALL_PLATFORM_NAMES)
    return [ai]
