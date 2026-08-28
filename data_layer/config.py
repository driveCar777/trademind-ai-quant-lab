import os

from data_layer.constants import DEFAULT_ALIASES, LOGICAL_SYMBOLS


def repo_root():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def load_data_sources(path=None):
    root = repo_root()
    cfg_path = path or os.path.join(root, "config", "data_sources.yaml")
    try:
        import yaml
    except Exception:
        yaml = None
    data = {}
    if yaml is not None and os.path.isfile(cfg_path):
        with open(cfg_path, "r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
    layer = data.get("data_layer") or {}
    storage_root = layer.get("storage_root") or "data/market"
    if not os.path.isabs(storage_root):
        storage_root = os.path.join(root, storage_root)
    aliases = layer.get("symbol_aliases") or DEFAULT_ALIASES
    return {
        "schema_version": str(layer.get("schema_version") or "0.1"),
        "timezone": layer.get("timezone") or "UTC",
        "storage_root": storage_root,
        "storage_policy": layer.get("storage_policy") or "single_immutable_copy",
        "bars_format": layer.get("bars_format") or "csv",
        "requested_bars": int(layer.get("requested_bars") or 2000),
        "request_slack_factor": float(layer.get("request_slack_factor") or 3.0),
        "rate_limit_seconds": float(layer.get("rate_limit_seconds") or 0.35),
        "terminal_path": ((layer.get("mt5") or {}).get("terminal_path")),
        "logical_symbols": tuple(layer.get("logical_symbols") or LOGICAL_SYMBOLS),
        "timeframes": tuple(layer.get("timeframes") or ("M15", "H1", "H4", "D1")),
        "symbol_aliases": aliases,
        "final_oos_locked": bool(layer.get("final_oos_locked", False)),
        "config_path": cfg_path,
    }
