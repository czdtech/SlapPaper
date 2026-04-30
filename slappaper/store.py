import json
import platform
import sys
import tempfile
from pathlib import Path

from slappaper.config import APP_NAME, DEFAULT_MOTTOS, SUPPORTED_PLATFORM


class MottoStoreError(RuntimeError):
    pass


def get_bundle_base_path():
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent


def get_store_path(system_name=None, home=None):
    system_name = system_name or platform.system()
    home = Path(home) if home is not None else Path.home()
    if system_name == SUPPORTED_PLATFORM:
        return home / "Library" / "Application Support" / APP_NAME / "motto.json"
    return home / f".{APP_NAME.lower()}" / "motto.json"


def get_settings_path(system_name=None, home=None):
    system_name = system_name or platform.system()
    home = Path(home) if home is not None else Path.home()
    if system_name == SUPPORTED_PLATFORM:
        return home / "Library" / "Application Support" / APP_NAME / "settings.json"
    return home / f".{APP_NAME.lower()}" / "settings.json"


def get_bundled_motto_path():
    return get_bundle_base_path() / "motto.json"


class MottoStore:
    def __init__(self, path=None, bundled_path=None):
        self.path = Path(path) if path is not None else get_store_path()
        self.bundled_path = (
            Path(bundled_path) if bundled_path is not None else get_bundled_motto_path()
        )

    def load_mottos(self):
        if self.path.exists():
            return self._read_mottos(self.path)
        return self.load_bundled_mottos()

    def load_runtime_mottos(self):
        try:
            mottos = self.load_mottos()
        except MottoStoreError:
            mottos = self.load_bundled_mottos()
        return mottos or DEFAULT_MOTTOS.copy()

    def load_bundled_mottos(self):
        try:
            mottos = self._read_mottos(self.bundled_path)
        except MottoStoreError:
            return DEFAULT_MOTTOS.copy()
        return mottos or DEFAULT_MOTTOS.copy()

    def add_motto(self, text):
        normalized = self._require_text(text)
        mottos = self.load_mottos()
        mottos.append(normalized)
        self._write_mottos(mottos)

    def update_motto(self, index, text):
        normalized = self._require_text(text)
        mottos = self.load_mottos()
        mottos[index] = normalized
        self._write_mottos(mottos)

    def delete_motto(self, index):
        mottos = self.load_mottos()
        mottos.pop(index)
        self._write_mottos(mottos)

    def _require_text(self, text):
        normalized = self._normalize(text)
        if not normalized:
            raise ValueError("Motto text cannot be empty.")
        return normalized

    def _normalize(self, text):
        if not isinstance(text, str):
            return ""
        return text.strip()

    def _read_mottos(self, path):
        try:
            with path.open("r", encoding="utf-8") as file_obj:
                data = json.load(file_obj)
        except FileNotFoundError as exc:
            raise MottoStoreError(f"Motto file is missing: {path}") from exc
        except json.JSONDecodeError as exc:
            raise MottoStoreError(f"Motto file is invalid JSON: {path}") from exc
        except OSError as exc:
            raise MottoStoreError(f"Unable to read motto file: {path}") from exc

        if not isinstance(data, list):
            raise MottoStoreError(f"Motto file must contain a JSON array: {path}")

        mottos = [self._normalize(item) for item in data]
        return [item for item in mottos if item]

    def _write_mottos(self, mottos):
        self._safe_write(self.path, mottos)

    def _safe_write(self, path, data):
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=path.parent,
            delete=False,
        ) as temp_file:
            json.dump(data, temp_file, ensure_ascii=False, indent=2)
            temp_file.write("\n")
            temp_path = Path(temp_file.name)
        temp_path.replace(path)


class SettingsStore:
    def __init__(self, path=None):
        self.path = Path(path) if path is not None else get_settings_path()

    def load_settings(self):
        if not self.path.exists():
            return {}
        try:
            with self.path.open("r", encoding="utf-8") as file_obj:
                data = json.load(file_obj)
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def get_setting(self, key, default=None):
        return self.load_settings().get(key, default)

    def set_setting(self, key, value):
        settings = self.load_settings()
        settings[key] = value
        self._write_settings(settings)

    def _write_settings(self, settings):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=self.path.parent,
            delete=False,
        ) as temp_file:
            json.dump(settings, temp_file, ensure_ascii=False, indent=2)
            temp_file.write("\n")
            temp_path = Path(temp_file.name)
        temp_path.replace(self.path)
