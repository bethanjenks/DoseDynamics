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
class CenterCrossingsResults:
    per_group: pd.DataFrame
    stats: list[dict]


class CenterCrossingsAnalysis:
    def __init__(self, cfg: Config, logger) -> None:
        self.cfg = cfg
        self.logger = logger
        self.paths = PathManager(cfg)

    def _compute_center_metrics(
        self,
        g: pd.DataFrame,
        center_x_min: float,
        center_x_max: float,
        center_y_min: float,
        center_y_max: float,
    ) -> dict:
        df2 = g[g["likelihood"] > self.cfg.preprocessing.likelihood_threshold].copy()
        df2["in_center"] = (
            (df2["x"] >= center_x_min)
            & (df2["x"] <= center_x_max)
            & (df2["y"] >= center_y_min)
            & (df2["y"] <= center_y_max)
        )

        ic = df2["in_center"].values
        entries = np.where(ic[1:] & ~ic[:-1])[0]
        exits = np.where(~ic[1:] & ic[:-1])[0]

        crossings = 0
        for e in entries:
            later_exits = exits[exits > e]
            if len(later_exits) == 0:
                continue
            exit_frame = later_exits[0]
            later_entries = entries[entries > exit_frame]
            if len(later_entries) > 0:
                crossings += 1

        return {
            "center_entries": len(entries),
            "center_exits": len(exits),
            "center_crossings": crossings,
        }

    def run(self) -> CenterCrossingsResults:
        data_full = load_h5(self.paths.resolve(self.cfg.input.h5_path))
        body_df = extract_body_part(
            data_full,
            body_part=self.cfg.input.body_part,
            meta_cols=self.cfg.input.meta_cols,
        )

        cutoff_frames = int(
            self.cfg.preprocessing.cutoff_minutes * 60 * self.cfg.preprocessing.fps
        )
        df_time = (
            body_df[
                body_df["likelihood"] >= self.cfg.preprocessing.likelihood_threshold
            ]
            .groupby(self.cfg.input.group_cols, group_keys=False)
            .apply(lambda g: g.head(cutoff_frames))
        )

        inner_frac = self.cfg.analysis.center_crossings.inner_frac
        center_x_min = (1 - inner_frac) / 2 * self.cfg.arena.width_cm
        center_x_max = self.cfg.arena.width_cm - center_x_min
        center_y_min = (1 - inner_frac) / 2 * self.cfg.arena.length_cm
        center_y_max = self.cfg.arena.length_cm - center_y_min

        results: List[dict] = []
        for _, g in df_time.groupby(self.cfg.input.group_cols):
            metrics = self._compute_center_metrics(
                g, center_x_min, center_x_max, center_y_min, center_y_max
            )
            for col in self.cfg.input.meta_cols:
                metrics[col] = g[col].iloc[0]
            results.append(metrics)

        center_df = pd.DataFrame(results)
        groups = {
            conc: g["center_crossings"].values
            for conc, g in center_df.groupby("concentration")
        }
        stats = perform_tests(
            groups, self.cfg.analysis.center_crossings.control_group, paired=False
        )

        return CenterCrossingsResults(per_group=center_df, stats=stats)
