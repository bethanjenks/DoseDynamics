from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from dosedynamics.analysis.stats import perform_tests
from dosedynamics.config import Config
from dosedynamics.io.loaders import load_h5
from dosedynamics.preprocessing.bodypart import extract_body_part
from dosedynamics.utils.paths import PathManager


@dataclass
class ThigmotaxisResults:
    per_group: pd.DataFrame
    stats: list[dict]


class ThigmotaxisAnalysis:
    def __init__(self, cfg: Config, logger) -> None:
        self.cfg = cfg
        self.logger = logger
        self.paths = PathManager(cfg)

    def _add_thigmotaxis_flag(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        width = self.cfg.arena.width_cm
        length = self.cfg.arena.length_cm
        margin_frac = self.cfg.analysis.thigmotaxis.margin_frac

        dist_left = df["x"]
        dist_right = width - df["x"]
        dist_bottom = df["y"]
        dist_top = length - df["y"]

        df["dist_from_wall"] = np.minimum.reduce(
            [dist_left, dist_right, dist_top, dist_bottom]
        )

        border_thickness = margin_frac * min(width, length)
        df["is_thigmo"] = df["dist_from_wall"] <= border_thickness
        return df

    def _compute_index(self, df: pd.DataFrame) -> pd.DataFrame:
        out = (
            df.groupby(self.cfg.input.group_cols)["is_thigmo"]
            .agg(thigmo_frames="sum", total_frames="count")
            .reset_index()
        )
        out["thigmotaxis_index"] = out["thigmo_frames"] / out["total_frames"]
        return out

    def _area_normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        width = self.cfg.arena.width_cm
        length = self.cfg.arena.length_cm
        margin_frac = self.cfg.analysis.thigmotaxis.margin_frac

        border_thickness = margin_frac * min(width, length)
        inner_w = width - 2 * border_thickness
        inner_l = length - 2 * border_thickness
        arena_area = width * length
        border_area = arena_area - inner_w * inner_l
        border_frac = border_area / arena_area

        df = df.copy()
        df["thigmo_area_norm"] = df["thigmotaxis_index"] / border_frac
        return df

    def run(self) -> ThigmotaxisResults:
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

        df_thig = self._add_thigmotaxis_flag(df_time)
        thig_df = self._compute_index(df_thig)

        for col in self.cfg.input.meta_cols:
            if col not in thig_df.columns and col in body_df.columns:
                thig_df[col] = (
                    body_df.groupby(self.cfg.input.group_cols)[col].first().values
                )

        if self.cfg.analysis.thigmotaxis.area_normalize:
            thig_df = self._area_normalize(thig_df)

        metric = self.cfg.analysis.thigmotaxis.metric
        groups = {c: g[metric].values for c, g in thig_df.groupby("concentration")}
        stats = perform_tests(
            groups, self.cfg.analysis.thigmotaxis.control_group, paired=False
        )

        return ThigmotaxisResults(per_group=thig_df, stats=stats)
