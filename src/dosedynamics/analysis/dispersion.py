from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import numpy as np
import pandas as pd

from dosedynamics.analysis.stats import get_cohens_d, perform_tests
from dosedynamics.config import Config
from dosedynamics.io.loaders import load_h5
from dosedynamics.preprocessing.bodypart import extract_body_part
from dosedynamics.preprocessing.mec import mec_time_bins
from dosedynamics.utils.paths import PathManager


@dataclass
class DispersionResults:
    per_bin: pd.DataFrame
    stats: list[dict]


class DispersionAnalysis:
    def __init__(self, cfg: Config, logger) -> None:
        self.cfg = cfg
        self.logger = logger
        self.paths = PathManager(cfg)

    def _compute_mec(self, g: pd.DataFrame) -> pd.DataFrame:
        mec = mec_time_bins(
            g[["x", "y", "likelihood"]],
            fps=self.cfg.preprocessing.fps,
            bin_seconds=self.cfg.analysis.dispersion.bin_seconds,
            max_minutes=self.cfg.preprocessing.cutoff_minutes,
            min_points=self.cfg.preprocessing.min_points,
            likelihood_thresh=self.cfg.preprocessing.likelihood_threshold,
        )
        for col in self.cfg.input.meta_cols:
            mec[col] = g[col].iat[0]
        return mec

    def run(self) -> DispersionResults:
        data_full = load_h5(self.paths.resolve(self.cfg.input.h5_path))
        body_df = extract_body_part(
            data_full,
            body_part=self.cfg.input.body_part,
            meta_cols=self.cfg.input.meta_cols,
        )

        mec_list: List[pd.DataFrame] = []
        for _, g in body_df.groupby(self.cfg.input.group_cols, sort=False):
            out = self._compute_mec(g)
            if len(out):
                mec_list.append(out)

        if not mec_list:
            raise ValueError("No MEC bins computed; check input data and config")

        mec_all = pd.concat(mec_list, ignore_index=True)
        mec_clean = mec_all.dropna(subset=["radius"])  # radius from mec_time_bins

        groups = {
            conc: g["radius"].values for conc, g in mec_clean.groupby("concentration")
        }
        stats = perform_tests(groups, self.cfg.analysis.dispersion.control_group, paired=False)

        return DispersionResults(per_bin=mec_clean, stats=stats)

    @staticmethod
    def get_effect_size(groups: Dict[str, np.ndarray], control: str, conc: str) -> float:
        return get_cohens_d(groups[conc], groups[control])
