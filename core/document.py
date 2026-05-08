import zipfile
import io
import json
from pathlib import Path
import numpy as np
from PIL import Image
from typing import List, Optional

from utils.errors import error_info

DOCUMENT_EXT = ".gtd"
DOCUMENT_TYPE = "Ground Truth PCB Analysis Document"
DOCUMENT_FORMAT_VERSION = 1
DOCUMENT_MODEL_VERSION = 1


class Document:

    def __init__(self, paths: Optional[List[str]] = None):
        self.clear()
        if paths:
            self.load_files(paths)

    def clear(self):
        self.images: List[np.ndarray] = []
        self.layers = []  # TODO: Placeholder

        self.metadata = {
            "extension": DOCUMENT_EXT,
            "document_type": DOCUMENT_TYPE,
            "format_version": DOCUMENT_FORMAT_VERSION,
            "model_version": DOCUMENT_MODEL_VERSION,
        }

        self._loaded_from_gtd = False
        self._gtd_path: Optional[Path] = Path("test.gtd") # TODO: Placeholder

    def is_loaded(self) -> bool:
        return self._loaded_from_gtd or len(self.images) >= 2

    def load_files(self, paths: List[str]):
        if self.is_loaded():
            return

        resolved = []
        for p in paths:
            try:
                resolved.append(Path(p).expanduser().resolve())
            except Exception:
                continue

        resolved = [p for p in resolved if p.exists() and p.is_file()]
        if not resolved:
            return

        gtd_files = [p for p in resolved if p.suffix.lower() == DOCUMENT_EXT]
        if gtd_files:
            self.load_gtd(gtd_files[0])
            return

        for path in resolved:
            if self.is_loaded():
                break
            self.load_image(path)

    def load_image(self, path: Path):
        if self.is_loaded():
            return

        try:
            with Image.open(path) as img:
                img = img.convert("RGB")
                data = np.array(img)
        except Exception as e:
            error_info("Image load error", f"Failed to load image:\n{path}\n\n{e}")
            return

        self.images.append(data)

    def save_gtd(self, path: Optional[Path] = None):
        if path is None:
            path = self._gtd_path

        if path is None or not path:
            error_info("Save error", "No save path specified.")
            return

        if path.suffix.lower() != DOCUMENT_EXT:
            path = Path(str(path) + DOCUMENT_EXT)

        try:
            with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:

                # ---------------- metadata ----------------
                zf.writestr(
                    "metadata.json",
                    json.dumps(self.metadata, indent=2)
                )

                # ---------------- images ----------------
                for i, img in enumerate(self.images):
                    pil_img = Image.fromarray(img, mode="RGB")

                    buf = io.BytesIO()
                    pil_img.save(buf, format="PNG", compress_level=4) # Compression levels 0-9, Max == 9
                    buf.seek(0)

                    zf.writestr(f"image_{i}.png", buf.read())

            self._gtd_path = path
            self._loaded_from_gtd = True

        except Exception as e:
            error_info("Save error", str(e))

    def load_gtd(self, path: Path):
        try:
            if not zipfile.is_zipfile(path):
                error_info("Load error", "Invalid .gtd file (not a zip archive)")
                return

            with zipfile.ZipFile(path, "r") as zf:

                # ---------------- Load ----------------
                try:
                    metadata = json.loads(zf.read("metadata.json").decode("utf-8"))
                except Exception as e:
                    error_info("Load error", f"Missing or invalid metadata\n{e}")
                    return

                image_files = sorted(
                    [f for f in zf.namelist() if f.startswith("image_") and f.endswith(".png")]
                )

                for i, image_file in enumerate (image_files):
                    raw = zf.read(image_file)

                    with Image.open(io.BytesIO(raw)) as img:
                        image_files[i] = np.array(img.convert("RGB"))

                # ---------------- Validate and apply ----------------
                if self.validate_gtd(metadata, image_files):

                    self.clear()
                    self.metadata = metadata
                    self._loaded_from_gtd = True
                    self._gtd_path = path
                    self.images = image_files

        except Exception as e:
            self.clear()
            error_info("Document load error", str(e))

    def validate_gtd(self, metadata, image_files):
        if (((metadata["extension"] != DOCUMENT_EXT or
                metadata["document_type"] !=DOCUMENT_TYPE) or
                len(image_files) != 2) or
                image_files[0].shape != image_files[1].shape):
            error_info("File validation error", "Not a valid GTD document")
            return False
        else:
            return True

    def flip(self, which, axis):
        self.images[which] = np.fliplr(self.images[which]) if axis == "h" else np.flipud(self.images[which])

    def rotate(self):
        self.images[0] = np.rot90(self.images[0], -1)
        self.images[1] = np.rot90(self.images[1], -1)
