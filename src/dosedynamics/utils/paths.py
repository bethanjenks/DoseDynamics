from __future__ import annotations

from pathlib import Path

from dosedynamics.config import Config


class PathManager:
    def __init__(self, cfg: Config) -> None:
        self.base_dir = Path(cfg.paths.base_dir)
        self.cfg = cfg

    def resolve(self, path: str) -> Path:
        p = Path(path)
        return p if p.is_absolute() else (self.base_dir / p)

    def data_raw_dir(self) -> Path:
        return self.resolve(self.cfg.paths.data_raw_dir)

    def data_interim_dir(self) -> Path:
        return self.resolve(self.cfg.paths.data_interim_dir)

    def data_processed_dir(self) -> Path:
        return self.resolve(self.cfg.paths.data_processed_dir)

    def reports_dir(self) -> Path:
        return self.resolve(self.cfg.paths.reports_dir)

    def figures_dir(self) -> Path:
        return self.resolve(self.cfg.paths.figures_dir)

    def logs_dir(self) -> Path:
        return self.resolve(self.cfg.paths.logs_dir)
