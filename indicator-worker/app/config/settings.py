from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseSettings


class Settings(BaseSettings):
    service_name: str = "indicator-worker"
    version: str = "1.0.0"
    build: str = "2026-07"
    worker_id: str = "xavier-worker-01"
    node_name: str = "xavier-01"
    node_role: str = "indicator"
    master_host: str = "localhost"
    master_port: int = 9000
    host: str = "0.0.0.0"
    api_port: int = 8080
    log_level: str = "INFO"
    config_file: str = "config/default.yaml"

    class Config:
        env_prefix = "TRADEMIND_"
        case_sensitive = False
        fields = {
            "api_port": {"env": "TRADEMIND_API_PORT"},
        }

    @classmethod
    def load(cls):
        settings = cls()
        config_path = Path(settings.config_file)
        if config_path.exists():
            with config_path.open("r", encoding="utf-8") as handle:
                data = yaml.safe_load(handle) or {}
            settings = cls(**{**settings.dict(), **data})
        return settings


@lru_cache()
def get_settings():
    return Settings.load()
