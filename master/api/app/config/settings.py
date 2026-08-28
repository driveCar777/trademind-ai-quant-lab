import os
from functools import lru_cache
from pathlib import Path

import yaml
from pydantic_settings import BaseSettings, SettingsConfigDict


def project_root() -> Path:
    return Path(__file__).resolve().parents[4]


class StorageSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    root: str = "data"
    workers_file: str = "workers.json"
    tasks_dir: str = "tasks"
    results_dir: str = "results"


class WorkerSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    request_timeout_seconds: int = 60


class AIGatewaySettings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    url: str = "http://127.0.0.1:9100"
    timeout_seconds: int = 120


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="TRADEMIND_",
        case_sensitive=False,
        extra="ignore",
    )

    service_name: str = "trademind-master"
    version: str = "1.2.0"
    host: str = "0.0.0.0"
    port: int = 9000
    log_level: str = "INFO"
    config_file: str = "config/default.yaml"
    storage: StorageSettings = StorageSettings()
    worker: WorkerSettings = WorkerSettings()
    ai_gateway: AIGatewaySettings = AIGatewaySettings()

    @property
    def data_root(self) -> Path:
        return project_root() / "data"

    @property
    def workers_path(self) -> Path:
        return self.data_root / self.storage.workers_file

    @property
    def tasks_path(self) -> Path:
        return self.data_root / self.storage.tasks_dir

    @property
    def results_path(self) -> Path:
        return self.data_root / self.storage.results_dir

    @classmethod
    def load(cls) -> "Settings":
        settings = cls()
        config_path = Path(settings.config_file)
        if not config_path.is_absolute():
            config_path = Path(__file__).resolve().parents[2] / config_path
        if config_path.exists():
            with config_path.open("r", encoding="utf-8") as handle:
                data = yaml.safe_load(handle) or {}
            settings = cls(**{**settings.model_dump(), **data})
        env_url = os.environ.get("TRADEMIND_AI_GATEWAY_URL")
        env_timeout = os.environ.get("TRADEMIND_AI_GATEWAY_TIMEOUT_SECONDS")
        if env_url or env_timeout:
            gateway = settings.ai_gateway.model_dump()
            if env_url:
                gateway["url"] = env_url
            if env_timeout:
                gateway["timeout_seconds"] = int(env_timeout)
            settings.ai_gateway = AIGatewaySettings(**gateway)
        return settings


@lru_cache()
def get_settings() -> Settings:
    return Settings.load()
