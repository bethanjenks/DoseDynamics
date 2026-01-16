from __future__ import annotations

from math import erfc, sqrt

import numpy as np
from scipy.stats import mannwhitneyu, wilcoxon


def perform_tests(groups, control, paired=False):
    out = []
    if control not in groups:
        raise ValueError(f"Control '{control}' not found")
    for conc, vals in groups.items():
        if conc == control:
            continue
        if paired:
            if len(groups[control]) != len(vals):
                raise ValueError("Paired test requires equal-length samples")
            stat, p = wilcoxon(groups[control], vals, alternative="two-sided")
            stat_name = "W_stat"
        else:
            stat, p = mannwhitneyu(groups[control], vals, alternative="two-sided")
            stat_name = "U_stat"
        out.append({"comparison": f"{control} vs {conc}", "conc_other": conc, stat_name: stat, "p_value": p})
    return out


def p_to_star(p: float) -> str:
    if p < 0.001:
        return "***"
    if p < 0.01:
        return "**"
    if p < 0.05:
        return "*"
    return "ns"


def get_cohens_d(x: np.ndarray, y: np.ndarray) -> float:
    nx, ny = len(x), len(y)
    if nx < 2 or ny < 2:
        return float("nan")
    vx, vy = np.var(x, ddof=1), np.var(y, ddof=1)
    pooled_sd = np.sqrt(((nx - 1) * vx + (ny - 1) * vy) / (nx + ny - 2))
    return (np.mean(x) - np.mean(y)) / pooled_sd
