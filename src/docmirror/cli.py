from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

import typer

from docmirror.config import load_config
from docmirror.context import RunContext
from docmirror.logging_utils import configure_logging
from docmirror.stages import analyze as analyze_stage
from docmirror.stages import preprocess as preprocess_stage
from docmirror.stages import render_docx as render_docx_stage
from docmirror.stages import run_all as run_all_stage
from docmirror.stages import validate as validate_stage
from docmirror.storage.ir_store import load_ir

app = typer.Typer(
    no_args_is_help=True,
    help="Convert structured JPG/JPEG documents into mirrored editable DOCX (scaffold).",
)

LOGGER = logging.getLogger(__name__)
DEFAULT_CONFIG = Path("config/default.yaml")


def _effective_config_path(config_path: Path | None) -> Path | None:
    if config_path is not None:
        return config_path
    if DEFAULT_CONFIG.exists():
        return DEFAULT_CONFIG
    return None


def _resolve_path(path: Path, output_dir: Path) -> Path:
    return path if path.is_absolute() else output_dir / path


def _build_context(
    input_path: Path,
    output_dir: Path,
    config_path: Path | None,
    debug: bool,
) -> RunContext:
    effective_config = _effective_config_path(config_path)
    config = load_config(effective_config)

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_dir.mkdir(parents=True, exist_ok=True)

    artifacts_dir = _resolve_path(config.paths.artifacts_dir, output_dir)
    logs_dir = _resolve_path(config.paths.logs_dir, output_dir)
    debug_dir = _resolve_path(config.paths.debug_dir, output_dir)

    artifacts_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    debug_dir.mkdir(parents=True, exist_ok=True)

    log_file = configure_logging(logs_dir=logs_dir, run_id=run_id, debug=debug)
    LOGGER.info("Run id: %s", run_id)
    if effective_config:
        LOGGER.info("Config loaded from: %s", effective_config)
    else:
        LOGGER.info("Config loaded from built-in defaults")
    LOGGER.info("Log file: %s", log_file)

    return RunContext(
        input_path=input_path,
        output_dir=output_dir,
        run_id=run_id,
        config=config,
        artifacts_dir=artifacts_dir,
        debug_dir=debug_dir,
        logs_dir=logs_dir,
        log_file=log_file,
    )


@app.command()
def preprocess(
    input_image: Path = typer.Argument(
        ...,
        exists=True,
        readable=True,
        help="Path to source JPG/JPEG image.",
    ),
    output_dir: Path = typer.Option(
        Path("out"),
        "--output-dir",
        "-o",
        help="Output root directory.",
    ),
    config: Path | None = typer.Option(
        None,
        "--config",
        "-c",
        exists=True,
        readable=True,
        help="Optional config file (.yaml/.yml/.toml).",
    ),
    debug: bool = typer.Option(False, "--debug", help="Enable debug logging."),
) -> None:
    context = _build_context(
        input_path=input_image, output_dir=output_dir, config_path=config, debug=debug
    )
    preprocessed = preprocess_stage.run(context=context, input_image=input_image)
    typer.echo(f"Preprocessed image: {preprocessed}")


@app.command()
def analyze(
    input_image: Path = typer.Argument(
        ...,
        exists=True,
        readable=True,
        help="Path to source JPG/JPEG image.",
    ),
    output_dir: Path = typer.Option(
        Path("out"), "--output-dir", "-o", help="Output root directory."
    ),
    preprocessed_image: Path | None = typer.Option(
        None,
        "--preprocessed-image",
        help="Optional preprocessed image path. If omitted, preprocess stage runs first.",
    ),
    config: Path | None = typer.Option(
        None,
        "--config",
        "-c",
        exists=True,
        readable=True,
        help="Optional config file (.yaml/.yml/.toml).",
    ),
    debug: bool = typer.Option(False, "--debug", help="Enable debug logging."),
) -> None:
    context = _build_context(
        input_path=input_image, output_dir=output_dir, config_path=config, debug=debug
    )
    image_for_analysis = preprocessed_image or preprocess_stage.run(
        context=context, input_image=input_image
    )
    _, ir_path = analyze_stage.run(
        context=context,
        preprocessed_image=image_for_analysis,
    )
    typer.echo(f"IR output: {ir_path}")


@app.command("render-docx")
def render_docx(
    ir_json: Path = typer.Argument(
        ...,
        exists=True,
        readable=True,
        help="Path to IR JSON produced by analyze.",
    ),
    output_dir: Path = typer.Option(
        Path("out"), "--output-dir", "-o", help="Output root directory."
    ),
    output_docx: Path | None = typer.Option(
        None,
        "--output-docx",
        help="Optional target DOCX path.",
    ),
    config: Path | None = typer.Option(
        None,
        "--config",
        "-c",
        exists=True,
        readable=True,
        help="Optional config file (.yaml/.yml/.toml).",
    ),
    debug: bool = typer.Option(False, "--debug", help="Enable debug logging."),
) -> None:
    context = _build_context(
        input_path=ir_json, output_dir=output_dir, config_path=config, debug=debug
    )
    ir = load_ir(ir_json)
    docx_path = render_docx_stage.run(context=context, ir=ir, output_docx=output_docx)
    typer.echo(f"DOCX output: {docx_path}")


@app.command()
def validate(
    source_image: Path = typer.Argument(
        ..., exists=True, readable=True, help="Path to source JPG/JPEG image."
    ),
    output_docx: Path = typer.Argument(
        ..., exists=True, readable=True, help="Path to generated DOCX."
    ),
    output_dir: Path = typer.Option(
        Path("out"), "--output-dir", "-o", help="Output root directory."
    ),
    ir_json: Path | None = typer.Option(
        None,
        "--ir-json",
        exists=True,
        readable=True,
        help="Optional IR JSON path used during rendering.",
    ),
    config: Path | None = typer.Option(
        None,
        "--config",
        "-c",
        exists=True,
        readable=True,
        help="Optional config file (.yaml/.yml/.toml).",
    ),
    debug: bool = typer.Option(False, "--debug", help="Enable debug logging."),
) -> None:
    context = _build_context(
        input_path=source_image, output_dir=output_dir, config_path=config, debug=debug
    )
    report_path = validate_stage.run(
        context=context,
        source_image=source_image,
        output_docx=output_docx,
        ir_json=ir_json,
    )
    typer.echo(f"Validation report: {report_path}")


@app.command("run-all")
def run_all(
    input_image: Path = typer.Argument(
        ...,
        exists=True,
        readable=True,
        help="Path to source JPG/JPEG image.",
    ),
    output_dir: Path = typer.Option(
        Path("out"), "--output-dir", "-o", help="Output root directory."
    ),
    config: Path | None = typer.Option(
        None,
        "--config",
        "-c",
        exists=True,
        readable=True,
        help="Optional config file (.yaml/.yml/.toml).",
    ),
    debug: bool = typer.Option(False, "--debug", help="Enable debug logging."),
) -> None:
    context = _build_context(
        input_path=input_image, output_dir=output_dir, config_path=config, debug=debug
    )
    docx_path, ir_path, report_path = run_all_stage.run(
        context=context,
        input_image=input_image,
    )
    typer.echo(f"DOCX output: {docx_path}")
    typer.echo(f"IR output: {ir_path}")
    typer.echo(f"Validation report: {report_path}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
