"""
image_processor.py — Resize and encode images for Gemma 4 multimodal input.

Gemma 4's vision encoder expects a fixed 336×336 RGB image.
This module handles:
  - Loading any common image format (JPEG, PNG, WEBP)
  - Resizing to 336×336 with aspect-ratio-preserving letterbox padding
  - Base64-encoding the result as a PNG byte string
  - OpenCV-based frame capture from the device camera
"""

import base64
import io
import logging
from pathlib import Path
from typing import Optional

from PIL import Image


TARGET_SIZE = (336, 336)


def load_and_encode(image_path: str) -> str:
    """
    Load an image from disk, resize to 336×336 with letterboxing,
    and return it as a base64-encoded PNG string.

    Parameters
    ----------
    image_path : str
        Absolute or relative path to the image file.

    Returns
    -------
    str — base64-encoded PNG suitable for injection into a data-URI:
          f"data:image/png;base64,{result}"
    """
    img = Image.open(image_path).convert("RGB")
    img = _letterbox(img, TARGET_SIZE)

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def capture_from_camera(save_path: Optional[str] = None) -> Optional[str]:
    """
    Capture a single frame from the default device camera using OpenCV.

    Parameters
    ----------
    save_path : str, optional
        If provided, the captured frame is saved to this path as a JPEG.
        Defaults to ./data/uploads/camera_capture.jpg.

    Returns
    -------
    str | None — path to the saved image, or None if capture failed.
    """
    try:
        import cv2
    except ImportError:
        logging.error("opencv-python not installed. Cannot capture from camera.")
        return None

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        logging.error("Could not open camera device.")
        return None

    ret, frame = cap.read()
    cap.release()

    if not ret or frame is None:
        logging.error("Failed to capture frame from camera.")
        return None

    if save_path is None:
        save_dir = Path("./data/uploads")
        save_dir.mkdir(parents=True, exist_ok=True)
        save_path = str(save_dir / "camera_capture.jpg")

    cv2.imwrite(save_path, frame)
    logging.info(f"Camera frame saved to {save_path}")
    return save_path


def _letterbox(img: Image.Image, target: tuple) -> Image.Image:
    """
    Resize image to fit within target dimensions, padding remainder with black
    so the aspect ratio is preserved and the output is exactly target size.
    """
    img.thumbnail(target, Image.LANCZOS)
    result = Image.new("RGB", target, (0, 0, 0))
    offset = ((target[0] - img.width) // 2, (target[1] - img.height) // 2)
    result.paste(img, offset)
    return result
