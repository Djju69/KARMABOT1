from __future__ import annotations

import logging
from logging.handlers import TimedRotatingFileHandler
import sys
from pathlib import Path


def setup_logging(level: int = logging.INFO, retention_days: int = 7, log_dir: str | None = None) -> None:
    """
    Configure root logger with stdout + timed rotating file handler.
    Old log files are automatically removed after `retention_days` via `backupCount`.

    Log files: <project_root>/logs/bot.log (unless log_dir specified)
    """
    root = logging.getLogger()
    root.setLevel(level)

    # Clear existing handlers (to avoid duplicates on reloads)
    for h in list(root.handlers):
        root.removeHandler(h)

    formatter = logging.Formatter(
        fmt="%(asctime)s - [%(levelname)s] - %(name)s - (%(filename)s).%(funcName)s(%(lineno)d) - %(message)s"
    )

    # Stdout handler
    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(level)
    sh.setFormatter(formatter)
    root.addHandler(sh)

    # File handler with daily rotation and retention
    try:
        base_dir = Path(log_dir) if log_dir else Path.cwd() / "logs"
        base_dir.mkdir(parents=True, exist_ok=True)
        log_path = base_dir / "bot.log"
        fh = TimedRotatingFileHandler(str(log_path), when="D", interval=1, backupCount=retention_days, encoding="utf-8")
        fh.setLevel(level)
        fh.setFormatter(formatter)
        root.addHandler(fh)
    except Exception as e:
        # Fail gracefully if FS not writable; stdout remains
        logging.getLogger(__name__).warning(f"File logging disabled: {e}")
