from __future__ import annotations

from typing import Dict, Iterable, List, Tuple

import numpy as np
import pandas as pd

from dosedynamics.analysis.arrest import detect_arrests_for_group
from dosedynamics.preprocessing.mec import mec_time_bins


def build_feature_names(
    base_features: Iterable[str],
    extra_features: Iterable[str],
) -> List[str]:
    names = list(base_features)
    names.extend(extra_features)
    return names


def _group_key(row: pd.Series, group_cols: List[str]) -> Tuple[str, ...]:
    return tuple(str(row[c]) for c in group_cols)


def _group_key_from_df(df: pd.DataFrame, group_cols: List[str]) -> Tuple[str, ...]:
    return tuple(str(df[c].iat[0]) for c in group_cols)


def compute_stops_lookup(
    data_full: pd.DataFrame,
    group_cols: List[str],
    fps: float,
    cutoff_minutes: float,
    stop_bin_seconds: float,
    min_still_seconds: float,
    movement_threshold: float,
    likelihood_threshold: float,
) -> Dict[Tuple[str, ...], pd.DataFrame]:
    lookup: Dict[Tuple[str, ...], pd.DataFrame] = {}
    cutoff_frames = int(cutoff_minutes * 60 * fps)
    frames_per_bin = int(stop_bin_seconds * fps)

    for _, g_full in data_full.groupby(group_cols):
        g_time = g_full.head(cutoff_frames)
        arrests = detect_arrests_for_group(
            g_time,
            fps=fps,
            min_still_seconds=min_still_seconds,
            movement_threshold=movement_threshold,
            likelihood_threshold=likelihood_threshold,
        )

        n_bins = int(np.ceil(len(g_time) / frames_per_bin))
        stops_per_bin = pd.DataFrame({"bin_id": np.arange(n_bins), "stops_per_bin": 0})

        if not arrests.empty:
            bin_ids = arrests["start_frame"] // frames_per_bin
            counts = bin_ids.value_counts().to_dict()
            for b, cnt in counts.items():
                if b < n_bins:
                    stops_per_bin.loc[stops_per_bin["bin_id"] == b, "stops_per_bin"] = (
                        cnt
                    )

        lookup[_group_key_from_df(g_time, group_cols)] = stops_per_bin

    return lookup


def compute_bin_features(
    g: pd.DataFrame,
    stops_lookup: Dict[Tuple[str, ...], pd.DataFrame],
    group_cols: List[str],
    meta_cols: List[str],
    fps: float,
    cutoff_minutes: float,
    bin_seconds: float,
    likelihood_threshold: float,
    min_points: int,
) -> pd.DataFrame:
    cutoff_frames = int(cutoff_minutes * 60 * fps)
    frames_per_bin = int(bin_seconds * fps)

    g = g.head(cutoff_frames)
    g = g[g["likelihood"] >= likelihood_threshold].copy()
    if len(g) < 2:
        return pd.DataFrame()

    g = g.reset_index(drop=True)

    g["step_dist"] = np.sqrt(g["x"].diff() ** 2 + g["y"].diff() ** 2).fillna(0)
    g["speed_cms"] = g["step_dist"] * fps
    g["bin_id"] = g.index // frames_per_bin

    speed_mean = g.groupby("bin_id")["speed_cms"].mean().rename("speed_cms")
    dist_mean = g.groupby("bin_id")["dist_from_wall"].mean().rename("dist_from_wall")
    agg = pd.concat([speed_mean, dist_mean], axis=1).reset_index()

    mec_df = mec_time_bins(
        g[["x", "y", "likelihood"]],
        fps=fps,
        bin_seconds=bin_seconds,
        max_minutes=None,
        min_points=min_points,
        likelihood_thresh=None,
    ).rename(columns={"radius": "mec_radius"})
    agg = agg.merge(mec_df[["bin_id", "mec_radius"]], on="bin_id", how="left")

    group_key = _group_key_from_df(g, group_cols)
    stops_df = stops_lookup.get(
        group_key, pd.DataFrame(columns=["bin_id", "stops_per_bin"])
    )
    agg = agg.merge(stops_df, on="bin_id", how="left")
    agg["stops_per_bin"] = agg["stops_per_bin"].fillna(0)

    for col in meta_cols:
        agg[col] = g[col].iat[0]

    return agg


def add_group_id(df: pd.DataFrame, group_cols: List[str], sep: str) -> pd.DataFrame:
    df = df.copy()
    df["group_id"] = df[group_cols].astype(str).agg(sep.join, axis=1)
    return df
