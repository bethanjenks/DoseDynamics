from __future__ import annotations

from typing import Dict, List

import numpy as np
import tensorly as tl
from tensorly.decomposition import parafac


def build_tensor(
    bin_df,
    features: List[str],
    group_id_col: str,
    bin_col: str,
) -> tuple[np.ndarray, List[Dict[str, str]], List[str], int]:
    groups = sorted(bin_df[group_id_col].unique().tolist())
    n_bins = int(bin_df[bin_col].max()) + 1
    X = np.full((len(groups), n_bins, len(features)), np.nan)

    meta = []
    for i, gid in enumerate(groups):
        sub = bin_df[bin_df[group_id_col] == gid]
        meta.append(
            {"group_id": gid, "concentration": str(sub["concentration"].iat[0])}
        )
        for _, row in sub.iterrows():
            b = int(row[bin_col])
            for feat_idx, feat in enumerate(features):
                X[i, b, feat_idx] = row.get(feat, np.nan)

    return X, meta, features, n_bins


def fill_tensor(X: np.ndarray, strategy: str, fill_value: float) -> np.ndarray:
    X_filled = X.copy()
    if strategy != "median":
        raise ValueError(f"Unsupported fill strategy: {strategy}")
    for f in range(X.shape[2]):
        feat_vals = X[:, :, f]
        median_val = np.nanmedian(feat_vals)
        if np.isnan(median_val):
            median_val = fill_value
        X_filled[:, :, f] = np.where(np.isnan(feat_vals), median_val, feat_vals)
    return X_filled


def run_tca(
    X: np.ndarray,
    rank: int,
    max_iter: int,
    tol: float,
    init: str,
    normalize_factors: bool,
    l2_reg: float,
) -> tuple[np.ndarray, List[np.ndarray]]:
    tl.set_backend("numpy")
    weights, factors = parafac(
        X,
        rank=rank,
        n_iter_max=max_iter,
        init=init,
        tol=tol,
        normalize_factors=normalize_factors,
        l2_reg=l2_reg,
    )
    return weights, factors
