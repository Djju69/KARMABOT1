import json
import os
import shutil
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

try:
    from jsonschema import validate, ValidationError  # type: ignore
except Exception:  # jsonschema опционален на рантайме, но желателен
    validate = None  # type: ignore
    ValidationError = Exception  # type: ignore

_MODULE_DIR = Path(__file__).resolve().parent  # ops/

def _resolve_path(env_key: str, default_name: str) -> Path:
    """Resolve path preferring env; if relative or missing, anchor at module dir (ops/)."""
    val = os.getenv(env_key)
    if val:
        p = Path(val)
        return p if p.is_absolute() else (_MODULE_DIR / p).resolve()
    return (_MODULE_DIR / default_name).resolve()

_DEFAULT_PATH = _resolve_path("SESSION_STATE_PATH", "SESSION_STATE.json")
_SCHEMA_PATH = _resolve_path("SESSION_STATE_SCHEMA_PATH", "SESSION_STATE.schema.json")
_ROTATE_COUNT = int(os.getenv("SESSION_STATE_ROTATE_N", "5") or 5)
_VERSION = os.getenv("APP_VERSION", "v2.4.2")
_NODE_ID = os.getenv("NODE_ID", os.getenv("HOSTNAME", "api-1"))

_lock = threading.RLock()
_state: Dict[str, Any] = {
    "version": _VERSION,
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "node_id": _NODE_ID,
    "build": {},
    "components": {}
}


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_parent(p: Path) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)


def _load_schema() -> Optional[Dict[str, Any]]:
    try:
        if _SCHEMA_PATH.is_file():
            with _SCHEMA_PATH.open("r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return None


def load(path: Optional[Path] = None) -> Dict[str, Any]:
    """Load state from disk with schema validation. On error, keep current in-memory state."""
    global _state
    p = (path or _DEFAULT_PATH)
    if not p.exists():
        # initialize fresh state
        _state["generated_at"] = _utcnow_iso()
        return _state
    try:
        with _lock:
            with p.open("r", encoding="utf-8") as f:
                data = json.load(f)
            # Validate if possible
            schema = _load_schema()
            if schema and validate:
                try:
                    validate(instance=data, schema=schema)
                except ValidationError:
                    # мягкая деградация — принимаем файл, игнорируя незнакомые поля
                    pass
            _state = data
            # Ensure required top-level fields exist
            _state.setdefault("version", _VERSION)
            _state.setdefault("generated_at", _utcnow_iso())
            _state.setdefault("node_id", _NODE_ID)
            _state.setdefault("components", {})
            return _state
    except Exception:
        # keep current state
        return _state


def snapshot() -> Dict[str, Any]:
    with _lock:
        # Обновляем generated_at на снимке
        cp = dict(_state)
        cp["generated_at"] = _utcnow_iso()
        return cp


def update(path: Optional[Path] = None, *, set_path: Optional[str] = None, value: Any = None, patch: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Update in-memory state. Either set a nested path (dot-delimited) to value, or deep-merge a patch under components.
    """
    global _state
    with _lock:
        if set_path is not None:
            parts = [p for p in set_path.split(".") if p]
            ref = _state
            for i, k in enumerate(parts):
                if i == len(parts) - 1:
                    ref[k] = value
                else:
                    if k not in ref or not isinstance(ref[k], dict):
                        ref[k] = {}
                    ref = ref[k]
        if patch:
            comp = _state.setdefault("components", {})
            # shallow merge patch into components
            for k, v in patch.items():
                if isinstance(v, dict):
                    comp.setdefault(k, {})
                    comp[k].update(v)
                else:
                    comp[k] = v
        _state["generated_at"] = _utcnow_iso()
        return dict(_state)


def _rotate_files(p: Path) -> None:
    try:
        base = p.parent
        stem = p.stem
        suffix = p.suffix  # .json
        # формируем имя с таймштампом
        ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        rotated = base / f"{stem}-{ts}{suffix}"
        if p.exists():
            shutil.copy2(p, rotated)
        # удалить старые, оставив последние N
        files = sorted(base.glob(f"{stem}-*{suffix}"), reverse=True)
        for idx, file in enumerate(files):
            if idx >= _ROTATE_COUNT:
                try:
                    file.unlink(missing_ok=True)
                except Exception:
                    pass
    except Exception:
        pass


def save(path: Optional[Path] = None) -> Path:
    """Atomic save with rotation: write to .tmp, fsync, rename()."""
    p = (path or _DEFAULT_PATH)
    tmp = p.with_suffix(p.suffix + ".tmp")
    with _lock:
        try:
            _ensure_parent(p)
            # Rotate previous file (best-effort)
            _rotate_files(p)
            data = snapshot()
            with tmp.open("w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, separators=(",", ":"), sort_keys=False)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, p)
        finally:
            try:
                if tmp.exists():
                    tmp.unlink(missing_ok=True)
            except Exception:
                pass
    return p


def mark_webhook_ui_refresh(reason: Optional[str] = None, ts: Optional[datetime] = None) -> None:
    dt = (ts or datetime.now(timezone.utc)).isoformat()
    update(patch={
        "webhooks": {
            "ui_refresh_menu": {
                "last_processed_ts": dt,
                "last_reason": reason or ""
            }
        }
    })


def mark_authme_cache_invalidation(ttl_sec: Optional[int] = None, reason: Optional[str] = None) -> None:
    comp = {
        "authme_cache": {
            "ttl_sec": int(ttl_sec or int(os.getenv("AUTHME_CACHE_TTL_SEC", "8"))),
            "last_invalidation_at": _utcnow_iso(),
        }
    }
    if reason:
        comp["authme_cache"]["last_reasons"] = [reason]
    update(patch=comp)
