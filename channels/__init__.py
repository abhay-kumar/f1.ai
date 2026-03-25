"""
Channel configuration loader.

Each channel (f1, history, science, food) has its own config file in this
directory exporting a CHANNEL dict with all channel-specific data: branding,
colors, themes, knowledge base, upload metadata, and credential paths.

Resolution order:
  1. Explicit channel_id argument
  2. script.json["channel"] (when loading from project)
  3. ITI_CHANNEL environment variable
  4. Default: "f1"
"""

import importlib
import json
import os

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SHARED_DIR = os.path.join(_BASE_DIR, "shared")
_cache = {}


def load_channel(channel_id: str = None) -> dict:
    """Load a channel config by ID. Caches after first load."""
    cid = channel_id or os.environ.get("ITI_CHANNEL", "f1")
    if cid not in _cache:
        mod = importlib.import_module(f"channels.{cid}")
        _cache[cid] = mod.CHANNEL
    return _cache[cid]


def load_channel_from_script(script: dict) -> dict:
    """Load channel config from a script.json dict."""
    return load_channel(script.get("channel"))


def channel_asset(channel: dict, *path_parts: str) -> str:
    """Resolve an asset path under shared/channels/<id>/."""
    return os.path.join(_SHARED_DIR, "channels", channel["id"], *path_parts)


def channel_cred(channel: dict, filename: str) -> str:
    """Resolve a credential path under shared/creds/<id>/."""
    return os.path.join(_SHARED_DIR, "creds", channel["id"], filename)


def shared_cred(filename: str) -> str:
    """Resolve a shared credential path (API keys used across channels)."""
    return os.path.join(_SHARED_DIR, "creds", filename)
