from __future__ import annotations

from dataclasses import dataclass
from typing import List

import pandas as pd

from dosedynamics.analysis.arrest import detect_arrests_for_group
from dosedynamics.analysis.stats import perform_tests
from dosedynamics.config import Config
from dosedynamics.io.loaders import load_h5
from dosedynamics.utils.paths import PathManager


@dataclass
class ArrestResults:
    arrests: pd.DataFrame
    stops_per_session: pd.DataFrame
    mean_duration_per_session: pd.DataFrame
    stats_stops: list[dict]
    stats_duration: list[dict]


class ArrestAnalysis:
    def __init__(self, cfg: Config, logger) -> None:
        self.cfg = cfg
        self.logger = logger
        self.paths = PathManager(cfg)

    def run(self) -> ArrestResults:
        data_full = load_h5(self.paths.resolve(self.cfg.input.h5_path))
        meta_cols = self.cfg.input.meta_cols
        group_cols = self.cfg.input.group_cols
        extra_cols = [c for c in meta_cols if c not in group_cols]
        group_by_cols = group_cols + extra_cols

        arrest_list: List[pd.DataFrame] = []
        cutoff_frames = int(
            self.cfg.preprocessing.cutoff_minutes * 60 * self.cfg.preprocessing.fps
        )

        for _, g in data_full.groupby(group_by_cols, sort=False):
            g_time = g.head(cutoff_frames)
            arrests = detect_arrests_for_group(
                g_time,
                fps=self.cfg.preprocessing.fps,
                min_still_seconds=self.cfg.arrest.min_still_seconds,
                movement_threshold=self.cfg.arrest.movement_threshold,
                likelihood_threshold=self.cfg.preprocessing.likelihood_threshold,
            )
            if arrests.empty:
                continue
            for col in meta_cols:
                arrests[col] = g_time[col].iloc[0]
            arrest_list.append(arrests)

        if arrest_list:
            arrests_all = pd.concat(arrest_list, ignore_index=True)
        else:
            arrests_all = pd.DataFrame(
                columns=[
                    "start_frame",
                    "end_frame",
                    "duration_frames",
                    "duration_s",
                ]
                + meta_cols
            )

        if arrests_all.empty:
            empty_stats: list[dict] = []
            return ArrestResults(
                arrests=arrests_all,
                stops_per_session=pd.DataFrame(),
                mean_duration_per_session=pd.DataFrame(),
                stats_stops=empty_stats,
                stats_duration=empty_stats,
            )

        stops_per_session = (
            arrests_all.groupby(group_by_cols).size().reset_index(name="n_stops")
        )

        mean_duration_per_session = (
            arrests_all.groupby(group_by_cols)
            .agg(mean_stop_duration_s=("duration_s", "mean"))
            .reset_index()
        )

        groups_stops = {
            conc: g["n_stops"].values
            for conc, g in stops_per_session.groupby("concentration")
        }
        stats_stops = perform_tests(
            groups_stops,
            self.cfg.analysis.arrest_analysis.control_group,
            paired=self.cfg.analysis.arrest_analysis.paired,
        )

        groups_duration = {
            conc: g["mean_stop_duration_s"].values
            for conc, g in mean_duration_per_session.groupby("concentration")
        }
        stats_duration = perform_tests(
            groups_duration,
            self.cfg.analysis.arrest_analysis.control_group,
            paired=self.cfg.analysis.arrest_analysis.paired,
        )

        return ArrestResults(
            arrests=arrests_all,
            stops_per_session=stops_per_session,
            mean_duration_per_session=mean_duration_per_session,
            stats_stops=stats_stops,
            stats_duration=stats_duration,
        )
