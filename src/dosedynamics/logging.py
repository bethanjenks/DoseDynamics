import logging
from pathlib import Path

from dosedynamics.config import Config
from dosedynamics.utils.paths import PathManager


def setup_logging(cfg: Config) -> logging.Logger:
    logger = logging.getLogger("dosedynamics")
    logger.setLevel(cfg.logging.level)
    logger.handlers.clear()

    log_dir = PathManager(cfg).logs_dir()
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / cfg.logging.log_file

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)

    file_handler = logging.FileHandler(Path(log_path))
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    logger.debug("Logging initialized")
    return logger
