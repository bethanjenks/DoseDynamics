from __future__ import annotations

import cv2
import numpy as np
import pandas as pd


def transform_dlc_coords_to_cm(df: pd.DataFrame, matrix: np.ndarray) -> pd.DataFrame:
    df_cm = df.copy()

    xy_cols_mask = df_cm.columns.get_level_values("coords").isin(["x", "y"])
    xy_df = df_cm.loc[:, xy_cols_mask]

    n_frames = len(df_cm)
    n_xy_cols = xy_df.shape[1]
    if n_xy_cols % 2 != 0:
        raise ValueError("Number of x/y columns must be even")

    pts = xy_df.to_numpy().astype(np.float32)
    pts = pts.reshape(-1, 2)
    pts = pts.reshape(-1, 1, 2)

    new_pts = cv2.perspectiveTransform(pts, matrix).reshape(-1, 2)
    new_xy = new_pts.reshape(n_frames, n_xy_cols)
    df_cm.loc[:, xy_cols_mask] = new_xy

    return df_cm
