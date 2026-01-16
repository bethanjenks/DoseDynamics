from __future__ import annotations

from typing import Optional

import cv2
import numpy as np
import pandas as pd


def mec_time_bins(
    mouse_df: pd.DataFrame,
    fps: float,
    bin_seconds: float,
    max_minutes: Optional[float],
    min_points: int,
    likelihood_thresh: Optional[float],
) -> pd.DataFrame:
    df = mouse_df.copy()

    if max_minutes is not None:
        cutoff_frames = int(max_minutes * 60 * fps)
        df = df.head(cutoff_frames)

    if likelihood_thresh is not None and "likelihood" in df.columns:
        df = df[df["likelihood"] >= likelihood_thresh]

    df = df.reset_index(drop=True)
    df.index.name = "frame"

    frames_per_bin = int(bin_seconds * fps)
    df["bin_id"] = df.index // frames_per_bin

    rows = []
    for b, chunk in df.groupby("bin_id"):
        chunk = chunk.dropna(subset=["x", "y"])
        if len(chunk) < min_points:
            start_f = int(b * frames_per_bin)
            end_f = int(min((b + 1) * frames_per_bin - 1, df.index.max()))
            rows.append(
                {
                    "bin_id": b,
                    "start_frame": start_f,
                    "end_frame": end_f,
                    "time_center_s": (start_f + end_f) / 2 / fps,
                    "center_x": np.nan,
                    "center_y": np.nan,
                    "radius": np.nan,
                    "area_cm2": np.nan,
                    "n_points": len(chunk),
                }
            )
            continue

        pts = chunk[["x", "y"]].to_numpy().astype(np.float32).reshape(-1, 1, 2)
        (cx, cy), r = cv2.minEnclosingCircle(pts)

        start_f = int(chunk.index.min())
        end_f = int(chunk.index.max())

        rows.append(
            {
                "bin_id": b,
                "start_frame": start_f,
                "end_frame": end_f,
                "time_center_s": (start_f + end_f) / 2 / fps,
                "center_x": float(cx),
                "center_y": float(cy),
                "radius": float(r),
                "area_cm2": float(np.pi * r**2),
                "n_points": len(chunk),
            }
        )

    return pd.DataFrame(rows).sort_values("bin_id").reset_index(drop=True)
