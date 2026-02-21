from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from docmirror.config import AppConfig


@dataclass(slots=True)
class RunContext:
    input_path: Path
    output_dir: Path
    run_id: str
    config: AppConfig
    artifacts_dir: Path
    debug_dir: Path
    logs_dir: Path
    log_file: Path
