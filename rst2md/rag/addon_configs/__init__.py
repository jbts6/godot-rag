"""Per-addon configuration registry.

Each addon can have its own .py file in this directory to define:
- smoke_queries: list of (query, expected_addon) for validation
- custom_doc_dirs: extra doc directories to discover
- custom_example_dirs: extra example directories to discover
- skip_doc_dirs: doc directories to exclude

Addons without a config file use auto-discovery defaults.
To add a new addon config, create a new .py file here — no need to modify other files.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class AddonConfig:
    """Configuration for a single addon."""
    name: str                           # Addon directory name (e.g. "scene_manager")
    display_name: Optional[str] = None  # Override plugin.cfg name
    smoke_queries: List[Tuple[str, str]] = field(default_factory=list)  # (query, addon_name)
    custom_doc_dirs: List[str] = field(default_factory=list)            # Relative to addon root
    custom_example_dirs: List[str] = field(default_factory=list)
    skip_doc_dirs: List[str] = field(default_factory=list)


_REGISTRY: dict[str, AddonConfig] = {}


def register(config: AddonConfig) -> None:
    """Register an addon configuration."""
    _REGISTRY[config.name] = config


def get_config(name: str) -> Optional[AddonConfig]:
    """Get config for an addon, or None if not registered."""
    return _REGISTRY.get(name)


def all_configs() -> dict[str, AddonConfig]:
    """Return all registered configs."""
    return dict(_REGISTRY)


def all_smoke_queries() -> List[Tuple[str, str]]:
    """Collect smoke queries from all registered configs."""
    queries = []
    for config in _REGISTRY.values():
        queries.extend(config.smoke_queries)
    return queries


def _auto_discover() -> None:
    """Import all .py files in this directory to trigger register() calls."""
    import importlib
    import pkgutil
    package_dir = __path__
    for _importer, module_name, _is_pkg in pkgutil.iter_modules(package_dir):
        if module_name != "__init__":
            importlib.import_module(f".{module_name}", __package__)


_auto_discover()
