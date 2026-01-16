from __future__ import annotations

from dataclasses import dataclass
from typing import List

import pandas as pd

from dosedynamics.analysis.features import (
    add_group_id,
    build_feature_names,
    compute_bin_features,
    compute_stops_lookup,
)
from dosedynamics.analysis.tca import build_tensor, fill_tensor, run_tca
from dosedynamics.config import Config
from dosedynamics.io.loaders import load_h5
from dosedynamics.io.savers import save_dataframe
from dosedynamics.preprocessing.arena import add_dist_from_wall
from dosedynamics.preprocessing.bodypart import extract_body_part
from dosedynamics.utils.paths import PathManager


@dataclass
class TCAResults:
    bin_df: pd.DataFrame
    factors: List
    features: List[str]
    n_bins: int
    meta: List[dict]


class TCAPerAnimalAnalysis:
    def __init__(self, cfg: Config, logger) -> None:
        self.cfg = cfg
        self.logger = logger
        self.paths = PathManager(cfg)

    def prepare_bin_df(self) -> pd.DataFrame:
        data_full = load_h5(self.paths.resolve(self.cfg.input.h5_path))

        body_df = extract_body_part(
            data_full,
            body_part=self.cfg.input.body_part,
            meta_cols=self.cfg.input.meta_cols,
        )
        body_df = add_dist_from_wall(
            body_df,
            self.cfg.arena.width_cm,
            self.cfg.arena.length_cm,
        )

        stops_lookup = compute_stops_lookup(
            data_full,
            group_cols=self.cfg.input.group_cols,
            fps=self.cfg.preprocessing.fps,
            cutoff_minutes=self.cfg.preprocessing.cutoff_minutes,
            stop_bin_seconds=self.cfg.analysis.tca.stop_bin_seconds,
            min_still_seconds=self.cfg.arrest.min_still_seconds,
            movement_threshold=self.cfg.arrest.movement_threshold,
            likelihood_threshold=self.cfg.preprocessing.likelihood_threshold,
        )

        bin_list = []
        for _, g in body_df.groupby(self.cfg.input.group_cols):
            out = compute_bin_features(
                g,
                stops_lookup=stops_lookup,
                group_cols=self.cfg.input.group_cols,
                meta_cols=self.cfg.input.meta_cols,
                fps=self.cfg.preprocessing.fps,
                cutoff_minutes=self.cfg.preprocessing.cutoff_minutes,
                bin_seconds=self.cfg.preprocessing.bin_seconds,
                likelihood_threshold=self.cfg.preprocessing.likelihood_threshold,
                min_points=self.cfg.preprocessing.min_points,
            )
            if len(out) > 0:
                bin_list.append(out)

        if not bin_list:
            raise ValueError("No bins produced; check input data and config")

        bin_df = pd.concat(bin_list, ignore_index=True)
        bin_df = add_group_id(bin_df, self.cfg.input.group_cols, sep="_")

        if self.cfg.output.save_processed:
            output_path = (
                self.paths.data_processed_dir() / self.cfg.output.processed_filename
            )
            save_dataframe(bin_df, output_path)
            self.logger.info("Saved processed bins to %s", output_path)

        return bin_df

    def run(self) -> TCAResults:
        bin_df = self.prepare_bin_df()

        feature_names = build_feature_names(
            base_features=self.cfg.analysis.tca.features.base,
            extra_features=self.cfg.analysis.tca.features.extra,
        )

        X, meta, features, n_bins = build_tensor(
            bin_df,
            features=feature_names,
            group_id_col="group_id",
            bin_col="bin_id",
        )
        X_filled = fill_tensor(
            X,
            self.cfg.analysis.tca.fill_strategy,
            self.cfg.analysis.tca.fill_value,
        )
        _, factors = run_tca(
            X_filled,
            rank=self.cfg.analysis.tca.rank,
            max_iter=self.cfg.analysis.tca.max_iter,
            tol=self.cfg.analysis.tca.tol,
            init=self.cfg.analysis.tca.init,
            normalize_factors=self.cfg.analysis.tca.normalize_factors,
            l2_reg=self.cfg.analysis.tca.l2_reg,
        )

        return TCAResults(
            bin_df=bin_df,
            factors=factors,
            features=features,
            n_bins=n_bins,
            meta=meta,
        )

    @staticmethod
    def build_loading_df(factors, meta: list[dict]) -> pd.DataFrame:
        mouse_f = factors[0]
        rows = []
        for i, m in enumerate(meta):
            for comp_idx in range(mouse_f.shape[1]):
                rows.append(
                    {
                        "group_id": m["group_id"],
                        "concentration": m["concentration"],
                        "component": comp_idx + 1,
                        "loading": mouse_f[i, comp_idx],
                    }
                )
        return pd.DataFrame(rows)
