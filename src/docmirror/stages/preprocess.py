from __future__ import annotations

import logging
from pathlib import Path

from docmirror.adapters.opencv_helper import preprocess_image
from docmirror.context import RunContext

LOGGER = logging.getLogger(__name__)


def run(context: RunContext, input_image: Path) -> Path:
    if not input_image.exists():
        raise FileNotFoundError(input_image)

    suffix = input_image.suffix.lower()
    if suffix not in {".jpg", ".jpeg"}:
        LOGGER.warning("Input extension %s is unusual for this pipeline.", suffix)

    output_image = context.debug_dir / f"{context.run_id}_preprocessed{suffix or '.jpg'}"
    preprocess_image(input_image=input_image, output_image=output_image)

    LOGGER.info("Preprocess output written to %s", output_image)
    return output_image
