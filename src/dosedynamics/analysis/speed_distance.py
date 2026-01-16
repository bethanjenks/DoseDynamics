from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import numpy as np
import pandas as pd

from dosedynamics.analysis.stats import perform_tests
from dosedynamics.config import Config
from dosedynamics.io.loaders import load_h5
from dosedynamics.preprocessing.bodypart import extract_body_part
from dosedynamics.utils.paths import PathManager


@dataclass
class SpeedDistanceResults:
    per_group: pd.DataFrame
    stats_by_metric: Dict[str, list[dict]]


class SpeedDistanceAnalysis:
    def __init__(self, cfg: Config, logger) -> None:
        self.cfg = cfg
        self.logger = logger
        self.paths = PathManager(cfg)

    def _compute_speed_distance(self, g: pd.DataFrame) -> pd.Series:
        cutoff_frames = int(self.cfg.preprocessing.cutoff_minutes * 60 * self.cfg.preprocessing.fps)
        g = g.head(cutoff_frames)
        g = g[g["likelihood"] >= self.cfg.preprocessing.likelihood_threshold]

        if g.empty:
            return pd.Series({
                "total_distance": np.nan,
                "mean_speed": np.nan,
                "frames_used": 0,
            })

        x = g["x"].to_numpy()
        y = g["y"].to_numpy()
        mask = ~np.isnan(x) & ~np.isnan(y)
        x = x[mask]
        y = y[mask]

        if len(x) < 2:
            return pd.Series({
                "total_distance": np.nan,
                "mean_speed": np.nan,
                "frames_used": len(g),
            })

        step_dist = np.sqrt(np.diff(x) ** 2 + np.diff(y) ** 2)
        total_dist = step_dist.sum()
        total_time = len(step_dist) / self.cfg.preprocessing.fps
        mean_speed = total_dist / total_time if total_time > 0 else np.nan

        return pd.Series({
            "total_distance": total_dist,
            "mean_speed": mean_speed,
            "frames_used": len(g),
        })

    def run(self) -> SpeedDistanceResults:
        data_full = load_h5(self.paths.resolve(self.cfg.input.h5_path))
        body_df = extract_body_part(
            data_full,
            body_part=self.cfg.input.body_part,
            meta_cols=self.cfg.input.meta_cols,
        )

        per_group = (
            body_df.groupby(self.cfg.input.group_cols, sort=False)
            .apply(self._compute_speed_distance)
            .reset_index()
        )

        for col in self.cfg.input.meta_cols:
            if col not in per_group.columns and col in body_df.columns:
                per_group[col] = body_df.groupby(self.cfg.input.group_cols)[col].first().values

        per_group = per_group.dropna(subset=["total_distance", "mean_speed"])

        stats_by_metric: Dict[str, list[dict]] = {}
        for metric in self.cfg.analysis.speed_distance.metrics.keys():
            groups = {
                c: g[metric].values for c, g in per_group.groupby("concentration")
            }
            stats_by_metric[metric] = perform_tests(
                groups, self.cfg.analysis.speed_distance.control_group, paired=False
            )

        return SpeedDistanceResults(per_group=per_group, stats_by_metric=stats_by_metric)
