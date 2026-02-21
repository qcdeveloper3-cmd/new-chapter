from __future__ import annotations

import shutil
from pathlib import Path


def preprocess_image(input_image: Path, output_image: Path) -> Path:
    output_image.parent.mkdir(parents=True, exist_ok=True)
    # TODO: Replace with real OpenCV pipeline:
    # - perspective correction
    # - deskew
    # - denoise and contrast normalization
    shutil.copy2(input_image, output_image)
    return output_image
