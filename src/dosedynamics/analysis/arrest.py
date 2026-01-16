from __future__ import annotations

from typing import Dict

import numpy as np
import pandas as pd


def detect_arrests_for_group(
    df_video: pd.DataFrame,
    fps: float,
    min_still_seconds: float,
    movement_threshold: float,
    likelihood_threshold: float,
) -> pd.DataFrame:
    pose_cols = [c for c in df_video.columns if isinstance(c, tuple)]
    if not pose_cols:
        return pd.DataFrame(
            columns=["start_frame", "end_frame", "duration_frames", "duration_s"]
        )

    pose_df = df_video[pose_cols].copy()
    cols = pose_df.columns
    bodyparts = sorted(cols.get_level_values("bodyparts").unique())

    positions: Dict[str, np.ndarray] = {}
    valid_mask: Dict[str, np.ndarray] = {}

    for bp in bodyparts:
        bp_mask = cols.get_level_values("bodyparts") == bp
        x_cols = cols[bp_mask & (cols.get_level_values("coords") == "x")]
        y_cols = cols[bp_mask & (cols.get_level_values("coords") == "y")]
        like_cols = cols[bp_mask & (cols.get_level_values("coords") == "likelihood")]

        if len(x_cols) == 0 or len(y_cols) == 0:
            continue

        x = pose_df[x_cols[0]].to_numpy()
        y = pose_df[y_cols[0]].to_numpy()

        if len(like_cols) > 0:
            lik = pose_df[like_cols[0]].to_numpy()
            good = lik >= likelihood_threshold
            x = np.where(good, x, np.nan)
            y = np.where(good, y, np.nan)

        pos = np.column_stack([x, y])
        positions[bp] = pos
        valid_mask[bp] = ~np.isnan(pos).any(axis=1)

    if not positions:
        return pd.DataFrame(
            columns=["start_frame", "end_frame", "duration_frames", "duration_s"]
        )

    n_frames = len(df_video)
    disp = np.zeros((n_frames, len(positions))) * np.nan

    for j, bp in enumerate(positions.keys()):
        pos = positions[bp]
        d = np.linalg.norm(np.diff(pos, axis=0), axis=1)
        d = np.insert(d, 0, np.nan)
        vm = valid_mask[bp]
        bad = ~(vm & np.r_[False, vm[:-1]])
        d[bad] = np.nan
        disp[:, j] = d

    still_bp = disp <= movement_threshold
    visible = ~np.isnan(disp)
    still_bp = np.where(visible, still_bp, True)
    visible_any = visible.any(axis=1)
    all_still = np.all(still_bp, axis=1) & visible_any

    min_still_frames = int(round(min_still_seconds * fps))
    arrests = []
    in_arrest = False
    start = None

    for i, flag in enumerate(all_still):
        if flag and not in_arrest:
            in_arrest = True
            start = i
        elif not flag and in_arrest:
            end = i - 1
            if end - start + 1 >= min_still_frames:
                arrests.append((start, end))
            in_arrest = False

    if in_arrest:
        end = n_frames - 1
        if end - start + 1 >= min_still_frames:
            arrests.append((start, end))

    rows = []
    for s, e in arrests:
        duration_frames = e - s + 1
        rows.append(
            {
                "start_frame": s,
                "end_frame": e,
                "duration_frames": duration_frames,
                "duration_s": duration_frames / fps,
            }
        )

    return pd.DataFrame(rows)
