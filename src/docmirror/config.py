from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover
    import tomli as tomllib


class PathConfig(BaseModel):
    artifacts_dir: Path = Path("artifacts")
    logs_dir: Path = Path("artifacts/logs")
    debug_dir: Path = Path("artifacts/debug")


class AnalysisConfig(BaseModel):
    primary_engine: Literal["docling"] = "docling"
    fallback_engine: str = "hybrid_ocr"
    enable_fallback_ocr: bool = True
    language_hints: list[str] = Field(default_factory=lambda: ["fa", "en"])


class RenderConfig(BaseModel):
    target_dpi: int = 300
    preserve_geometry: bool = True
    rtl_default: bool = True
    enable_mixed_direction_runs: bool = True
    font_preferences: dict[str, str] = Field(
        default_factory=lambda: {"fa": "B Nazanin", "en": "Calibri"}
    )


class ValidationConfig(BaseModel):
    enable_visual_diff: bool = True
    max_text_distance_ratio: float = 0.02
    max_bbox_shift_px: int = 4


class AppConfig(BaseModel):
    paths: PathConfig = Field(default_factory=PathConfig)
    analysis: AnalysisConfig = Field(default_factory=AnalysisConfig)
    render: RenderConfig = Field(default_factory=RenderConfig)
    validation: ValidationConfig = Field(default_factory=ValidationConfig)


def _load_raw_config(config_path: Path) -> dict[str, Any]:
    suffix = config_path.suffix.lower()
    if suffix in {".yaml", ".yml"}:
        with config_path.open("r", encoding="utf-8") as f:
            loaded = yaml.safe_load(f) or {}
        if not isinstance(loaded, dict):
            raise ValueError(f"YAML config must be a mapping: {config_path}")
        return loaded
    if suffix == ".toml":
        with config_path.open("rb") as f:
            loaded = tomllib.load(f)
        if not isinstance(loaded, dict):
            raise ValueError(f"TOML config must be a mapping: {config_path}")
        return loaded
    raise ValueError("Config file extension must be .yaml, .yml, or .toml")


def load_config(config_path: Path | None) -> AppConfig:
    if config_path is None:
        return AppConfig()
    raw = _load_raw_config(config_path)
    return AppConfig.model_validate(raw)
