from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from dosedynamics.analysis.stats import p_to_star
from dosedynamics.config import PlottingConfig, SpeedDistanceConfig


class SpeedDistancePlotter:
    def __init__(
        self, plot_cfg: PlottingConfig, speed_cfg: SpeedDistanceConfig
    ) -> None:
        self.plot_cfg = plot_cfg
        self.speed_cfg = speed_cfg

    def plot_metric(
        self,
        per_group: pd.DataFrame,
        metric: str,
        stats: list[dict],
    ) -> tuple:
        concs = [
            c
            for c in self.plot_cfg.plot_order
            if c in per_group["concentration"].unique()
        ]
        x = np.arange(len(concs))

        grouped = per_group.groupby("concentration")[metric]
        means = grouped.mean().loc[concs].values
        sems = grouped.sem().loc[concs].values

        fig, ax = plt.subplots(figsize=(8, 5))
        bar_colors = [self.plot_cfg.color_map.get(c, "gray") for c in concs]

        ax.bar(
            x,
            means,
            yerr=sems,
            capsize=5,
            alpha=0.8,
            color=bar_colors,
            edgecolor=self.plot_cfg.style.edge_color,
            linewidth=self.plot_cfg.style.line_width,
            zorder=1,
        )

        for i, conc in enumerate(concs):
            vals = per_group[per_group["concentration"] == conc][metric].values
            if len(vals) == 0:
                continue
            jitter = (np.random.rand(len(vals)) - 0.5) * self.plot_cfg.jitter.box
            ax.scatter(
                np.full(len(vals), i) + jitter,
                vals,
                color=self.plot_cfg.style.edge_color,
                s=self.plot_cfg.style.point_size,
                alpha=self.plot_cfg.style.point_alpha,
                zorder=10,
            )

        ax.set_xticks(x)
        ax.set_xticklabels(
            [self.plot_cfg.dose_labels.get(c, c) for c in concs], fontsize=12
        )
        ax.set_xlabel(self.plot_cfg.loadings.xlabel_dose, fontsize=12)
        ax.set_ylabel(self.speed_cfg.metrics[metric].ylabel, fontsize=12)
        ax.set_title(self.speed_cfg.metrics[metric].title, fontsize=13)

        ax.tick_params(axis="x", length=5, width=self.plot_cfg.style.line_width)
        ax.tick_params(axis="y", length=5, width=self.plot_cfg.style.line_width)
        for spine in ax.spines.values():
            spine.set_linewidth(self.plot_cfg.style.line_width)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        if stats:
            y_max = float(np.nanmax(means + sems))
            text_y = y_max * 1.2 if y_max > 0 else 1.0
            for row in stats:
                c = row["conc_other"]
                if c not in concs:
                    continue
                label = p_to_star(row["p_value"])
                x_pos = concs.index(c)
                ax.text(
                    x_pos,
                    text_y,
                    label,
                    ha="center",
                    va="bottom",
                    fontsize=12,
                    fontweight="bold",
                )
            ax.set_ylim(0, text_y * 1.1)

        fig.tight_layout()
        return fig, ax
