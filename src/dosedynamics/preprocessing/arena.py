from __future__ import annotations

import numpy as np
import pandas as pd


def add_dist_from_wall(
    df: pd.DataFrame, width_cm: float, length_cm: float
) -> pd.DataFrame:
    df = df.copy()
    dist_left = df["x"]
    dist_right = width_cm - df["x"]
    dist_bottom = df["y"]
    dist_top = length_cm - df["y"]
    df["dist_from_wall"] = np.minimum.reduce(
        [dist_left, dist_right, dist_bottom, dist_top]
    )
    return df
