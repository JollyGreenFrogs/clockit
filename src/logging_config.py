"""Centralized logging configuration for ClockIt.

Sets up a console handler and a rotating file handler under the data directory
specified by the CLOCKIT_DATA_DIR environment variable (defaults to ./clockit_data).
"""
import logging
import logging.handlers
import os
from pathlib import Path


def configure_logging(level: int = logging.INFO, log_filename: str = "clockit.log"):
    data_dir = Path(os.environ.get('CLOCKIT_DATA_DIR', './clockit_data'))
    try:
        data_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        # If we can't create the data directory, fall back to current working dir
        data_dir = Path('.')

    logger = logging.getLogger()
    logger.setLevel(level)

    # Avoid adding duplicate handlers if configure_logging is called multiple times
    if logger.handlers:
        return

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch_fmt = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(ch_fmt)
    logger.addHandler(ch)

    # Rotating file handler
    fh = logging.handlers.RotatingFileHandler(
        filename=str(data_dir / log_filename),
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding='utf-8'
    )
    fh.setLevel(level)
    fh.setFormatter(ch_fmt)
    logger.addHandler(fh)


__all__ = ['configure_logging']
