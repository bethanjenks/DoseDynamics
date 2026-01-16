from __future__ import annotations

from dataclasses import dataclass
from typing import List

import numpy as np
import pandas as pd

from dosedynamics.analysis.stats import perform_tests
from dosedynamics.config import Config
from dosedynamics.io.loaders import load_h5
from dosedynamics.preprocessing.bodypart import extract_body_part
from dosedynamics.utils.paths import PathManager


@dataclass
class SpeedBinsResults:
    bin_speeds: pd.DataFrame
    stats: list[dict]


class SpeedBinsAnalysis:
    def __init__(self, cfg: Config, logger) -> None:
        self.cfg = cfg
        self.logger = logger
        self.paths = PathManager(cfg)

    def _compute_bin_speeds(self, g: pd.DataFrame) -> pd.DataFrame:
        max_frames = int(self.cfg.preprocessing.cutoff_minutes * 60 * self.cfg.preprocessing.fps)
        frames_per_bin = int(self.cfg.analysis.speed_bins.bin_seconds * self.cfg.preprocessing.fps)

        g = g.head(max_frames)
        g = g[g["likelihood"] >= self.cfg.preprocessing.likelihood_threshold].copy()
        if len(g) < 2:
            return pd.DataFrame()

        g = g.reset_index(drop=True)
        step_dist = np.sqrt(g["x"].diff() ** 2 + g["y"].diff() ** 2)
        step_dist.iloc[0] = 0
        g["step_dist"] = step_dist
        g["bin_id"] = g.index // frames_per_bin

        agg = (
            g.groupby("bin_id")["step_dist"]
            .agg(total_distance="sum", n_frames="count")
            .reset_index()
        )
        agg["bin_speed"] = agg["total_distance"] / self.cfg.analysis.speed_bins.bin_seconds

        for col in self.cfg.input.meta_cols:
            agg[col] = g[col].iat[0]

        return agg

    def run(self) -> SpeedBinsResults:
        data_full = load_h5(self.paths.resolve(self.cfg.input.h5_path))
        body_df = extract_body_part(
            data_full,
            body_part=self.cfg.input.body_part,
            meta_cols=self.cfg.input.meta_cols,
        )

        bin_list: List[pd.DataFrame] = []
        for _, g in body_df.groupby(self.cfg.input.group_cols, sort=False):
            out = self._compute_bin_speeds(g)
            if len(out):
                bin_list.append(out)

        if not bin_list:
            raise ValueError("No bin speeds computed; check input data and config")

        bin_speeds = pd.concat(bin_list, ignore_index=True)
        bin_speeds = bin_speeds.dropna(subset=["bin_speed"])

        groups = {
            c: g["bin_speed"].values for c, g in bin_speeds.groupby("concentration")
        }
        stats = perform_tests(groups, self.cfg.analysis.speed_bins.control_group, paired=False)
        return SpeedBinsResults(bin_speeds=bin_speeds, stats=stats)
