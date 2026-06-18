"""Lightweight model registry for optional routing artifacts."""

from __future__ import annotations

import json
import pickle
import threading
from pathlib import Path
from typing import Any, Optional


BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"


def _load_serialized_artifact(path: Path) -> Any:
    try:
        import joblib  # type: ignore
    except ImportError:
        joblib = None

    if joblib is not None:
        return joblib.load(path)

    with path.open("rb") as handle:
        return pickle.load(handle)


class ModelRegistry:
    """Safe, cached access to optional local model artifacts."""

    def __init__(self, models_dir: Optional[Path] = None):
        self.models_dir = models_dir or MODELS_DIR
        self.intent_model_path = self.models_dir / "intent_classifier.joblib"
        self.intent_label_map_path = self.models_dir / "intent_label_map.json"
        self.router_thresholds_path = self.models_dir / "router_thresholds.json"
        self._lock = threading.Lock()
        self._intent_model_loaded = False
        self._intent_model = None
        self._intent_model_error: Optional[str] = None
        self._intent_label_map: Optional[dict[str, str]] = None
        self._router_thresholds: Optional[dict[str, Any]] = None

    def load_intent_classifier(self) -> Any:
        with self._lock:
            if self._intent_model_loaded:
                return self._intent_model
            self._intent_model_loaded = True
            if not self.intent_model_path.exists():
                self._intent_model = None
                return None
            try:
                self._intent_model = _load_serialized_artifact(self.intent_model_path)
            except Exception as exc:  # pragma: no cover - defensive fallback.
                self._intent_model_error = str(exc)
                self._intent_model = None
            return self._intent_model

    def load_intent_label_map(self) -> dict[str, str]:
        if self._intent_label_map is not None:
            return self._intent_label_map
        if not self.intent_label_map_path.exists():
            self._intent_label_map = {}
            return self._intent_label_map
        try:
            self._intent_label_map = json.loads(
                self.intent_label_map_path.read_text(encoding="utf-8")
            )
        except Exception:  # pragma: no cover - defensive fallback.
            self._intent_label_map = {}
        return self._intent_label_map

    def load_router_thresholds(self) -> dict[str, Any]:
        if self._router_thresholds is not None:
            return self._router_thresholds
        if not self.router_thresholds_path.exists():
            self._router_thresholds = {}
            return self._router_thresholds
        try:
            self._router_thresholds = json.loads(
                self.router_thresholds_path.read_text(encoding="utf-8")
            )
        except Exception:  # pragma: no cover - defensive fallback.
            self._router_thresholds = {}
        return self._router_thresholds

    @property
    def intent_model_error(self) -> Optional[str]:
        return self._intent_model_error


_DEFAULT_REGISTRY = ModelRegistry()


def get_model_registry() -> ModelRegistry:
    return _DEFAULT_REGISTRY
