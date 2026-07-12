import io
import json
import pickle
import shutil
import tempfile
import uuid
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image

from utils.errors import error_info
from core.annotations import Annotation

DOCUMENT_EXT = ".gtd"
DOCUMENT_TYPE = "Ground Truth PCB Analysis Document"
DOCUMENT_FORMAT_VERSION = 1
DOCUMENT_MODEL_VERSION = 1

DEFAULT_LAYER_COUNT = 10


class Document:

    DEFAULT_LAYER_COLORS = [
        "#e6194b",
        "#3cb44b",
        "#ffe119",
        "#4363d8",
        "#f58231",
        "#911eb4",
        "#46f0f0",
        "#f032e6",
        "#bcf60c",
        "#fabebe",
    ]

    def __init__(self, paths: list [str] |None = None):
        self.clear()
        if paths:
            [print(f"Error: {e}") for e in self.load_files(paths)]

    def clear(self):
        self.loaded = False
        self.images: list[np.ndarray] = []
        self.current_layer_index = 0
        self.layers = []
        for _ in range(DEFAULT_LAYER_COUNT):
            self.add_layer()

        self.metadata = {
            "extension": DOCUMENT_EXT,
            "document_type": DOCUMENT_TYPE,
            "format_version": DOCUMENT_FORMAT_VERSION,
            "model_version": DOCUMENT_MODEL_VERSION,
        }

        self.config = {
            "axis_inverted": ({"x": False, "y": False}, {"x": False, "y": False}),
        }
        self.saved_gtd = False
        self._gtd_path: Path | None = None

    def is_loaded(self) -> bool:
        return self.loaded

    def load_files(self, paths: list[str]):
        """ Tries to load the files from the list. Returns a list containing any load errors."""
        if len(self.images) > 1:
            return []

        errors = []
        resolved = []
        for p in paths:
            try:
                resolved_path = Path(p).expanduser().resolve()
                if resolved_path.exists() and resolved_path.is_file():
                    resolved.append(resolved_path)
                else:
                    errors.append(f"Could not resolve path to file: {p}")
            except Exception as e:
                errors.append(e)

        gtd_files = [p for p in resolved if p.suffix.lower() == DOCUMENT_EXT]
        if gtd_files:
            return self.__load_gtd(gtd_files[0])

        for path in resolved:
            if len(self.images) > 1:
                break
            err = self.__load_image(path)
            if err is not None:
                errors.append(err)

        return errors

    def __load_image(self, path: Path):
        try:
            with Image.open(path) as img:
                img = img.convert("RGB")
                data = np.array(img)
        except Exception as e:
            return f"Failed to load image:\n{path}\n\n{e}"

        if self.images:
            if data.shape != self.images[0].shape:
                return f"Image size mismatch, both images need to be of the same size"

        self.images.append(data)

    def __load_gtd(self, path: Path):
        try:
            if not zipfile.is_zipfile(path):
                return ["Invalid .gtd file - Underlying zip file structure not detected"]

            with zipfile.ZipFile(path, "r") as zf:

                # ---------------- Load ----------------
                try:
                    metadata = json.loads(zf.read("metadata.json").decode("utf-8"))
                    config = json.loads(zf.read("config.json").decode("utf-8"))
                except Exception as e:
                    return [f"Missing or invalid data files in gtd document: \n{e}"]

                layers_data = None
                if "layers.pkl" in zf.namelist():
                    try:
                        layers_data = pickle.loads(zf.read("layers.pkl"))
                    except Exception as e:
                        return [f"Unable to read layer information from file: \n{e}"]

                image_files = sorted(
                    [f for f in zf.namelist() if f.startswith("image_") and f.endswith(".jpg")]
                )

                for i, image_file in enumerate(image_files):
                    raw = zf.read(image_file)

                    with Image.open(io.BytesIO(raw)) as img:
                        image_files[i] = np.array(img.convert("RGB"))

                # ---------------- Validate and apply ----------------
                if not self.__validate_gtd(metadata, image_files, layers_data):
                    return ["Not a valid gtd document"]

                self.metadata = metadata
                self.config = config
                self.saved_gtd = True
                self._gtd_path = path
                self.images = image_files
                if layers_data is not None:
                    self.layers = layers_data

                self.loaded = True

            return []

        except Exception as e:
            self.clear()
            return ["Document load error" + str(e)]

    def __validate_gtd(self, metadata, image_files, layers_data):
        if (((metadata["extension"] != DOCUMENT_EXT or
                metadata["document_type"] != DOCUMENT_TYPE) or
                len(image_files) != 2) or
                image_files[0].shape != image_files[1].shape):
            return False

        if not isinstance(layers_data, list):
            return False

        return True
    
    def add_layer(self):
        color = self.DEFAULT_LAYER_COLORS[len(self.layers) % len(self.DEFAULT_LAYER_COLORS)]
        self.layers.append(Layer(name=f"Layer {len(self.layers) + 1}", color=color))

    def save(self, target_path: str | None = None):
        updating = target_path is None

        if updating:
            target_path = Path(self._gtd_path).with_suffix(DOCUMENT_EXT)
            if not target_path.exists():
                error_info("Save error", "No existing file to update.")
                return
        elif isinstance(target_path, str):
            target_path = Path(target_path).with_suffix(DOCUMENT_EXT)
        else:
            error_info("Save error", "No save path specified.")
            return

        # To avoid always re-encoding images, copy existing images to a temp file on update
        try:
            with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
                tmp_path = Path(tmp.name)

            with zipfile.ZipFile(tmp_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:

                # ---------- metadata & config ----------
                zf.writestr("metadata.json", json.dumps(self.metadata, indent=2))
                zf.writestr("config.json", json.dumps(self.config, indent=2))
                zf.writestr("layers.pkl", pickle.dumps(self.layers))

                # ---------- images ----------
                if updating:
                    with zipfile.ZipFile(target_path, "r") as src:
                        for item in src.infolist():
                            if item.filename.startswith("image_") and item.filename.endswith(".jpg"):
                                zf.writestr(item, src.read(item.filename))
                else:
                    for i, img in enumerate(self.images):
                        pil_img = Image.fromarray(img, mode="RGB")
                        buf = io.BytesIO()
                        pil_img.save(buf, format="JPEG", quality=95, subsampling=0, optimize=True)
                        zf.writestr(f"image_{i}.jpg", buf.getvalue())

            shutil.move(tmp_path, target_path)

            self._gtd_path = target_path
            self.saved_gtd = True

        except Exception as e:
            error_info("Save error", str(e))
        finally:
            if tmp_path.exists():
                tmp_path.unlink(missing_ok=True)

    def flip(self, which, axis):
        self.images[which] = np.fliplr(self.images[which]) if axis == "h" else np.flipud(self.images[which])

    def rotate(self):
        self.images[0] = np.rot90(self.images[0], -1)
        self.images[1] = np.rot90(self.images[1], -1)

    def get_current_layer(self):
        return self.layers[self.current_layer_index]

    def get_file_name(self):
        return self._gtd_path.name


class Layer:

    def __init__(self, name: str, color: str, visible: bool = True, alpha: float = 0.8):
        self.uid = str(uuid.uuid4())
        self.name = name
        self.color = color
        self.visible = visible
        self.alpha = alpha
        self.items: list[Annotation] = []

    def __getitem__(self, key: int):
        return self.items[key]

    def get_annotations(self):
        return self.items

    def add_annotation(self, annotation: Annotation):
        self.items.append(annotation)

    def remove_annotation(self, annotation: Annotation):
        self.items = [item for item in self.items if item.uid != annotation.uid]

    def clear_annotations(self):
        self.items = []

    def is_empty(self):
        return len(self.get_annotations()) == 0

