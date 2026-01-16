from __future__ import annotations

from typing import Dict, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from dosedynamics.analysis.stats import p_to_star, perform_tests
from dosedynamics.config import PlottingConfig


class TCAPlotter:
    def __init__(
        self, plot_cfg: PlottingConfig, bin_seconds: float, control_group: str
    ) -> None:
        self.plot_cfg = plot_cfg
        self.bin_seconds = bin_seconds
        self.control_group = control_group

    def plot_factors(
        self,
        factors,
        meta: List[Dict[str, str]],
        features: List[str],
        n_bins: int,
    ) -> tuple:
        mouse_f, time_f, feat_f = factors
        rank = mouse_f.shape[1]

        fig, axes = plt.subplots(1, 3, figsize=self.plot_cfg.factors.fig_size)

        ax = axes[0]
        seen = {}
        for i, m in enumerate(meta):
            conc = m["concentration"]
            color = self.plot_cfg.color_map.get(conc, "gray")
            sc = ax.scatter(
                np.arange(rank)
                + (np.random.rand(rank) - 0.5) * self.plot_cfg.jitter.mouse,
                mouse_f[i, :],
                color=color,
                edgecolor=self.plot_cfg.style.edge_color,
                alpha=self.plot_cfg.style.point_alpha,
                s=self.plot_cfg.style.point_size,
                linewidths=self.plot_cfg.style.line_width,
            )
            seen.setdefault(conc, sc)
        ax.set_title(self.plot_cfg.factors.title_mouse)
        ax.set_xlabel(self.plot_cfg.factors.xlabel_component)
        ax.set_ylabel(self.plot_cfg.factors.ylabel_loading)
        ax.set_xticks(range(rank))
        ax.set_xticklabels([f"C{r + 1}" for r in range(rank)])
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        for spine in ax.spines.values():
            spine.set_linewidth(self.plot_cfg.style.line_width)
        handles = [seen[c] for c in self.plot_cfg.dose_labels if c in seen]
        labels = [
            f"{self.plot_cfg.dose_labels[c]} {self.plot_cfg.dose_unit}"
            for c in self.plot_cfg.dose_labels
            if c in seen
        ]
        if handles:
            ax.legend(handles, labels, frameon=False, fontsize=9, loc="upper right")

        ax = axes[1]
        t_axis = np.arange(n_bins) * self.bin_seconds
        for r in range(rank):
            ax.plot(
                t_axis,
                time_f[:, r],
                label=f"C{r + 1}",
                linewidth=self.plot_cfg.style.factor_line_width,
            )
        ax.set_title(self.plot_cfg.factors.title_time)
        ax.set_xlabel(self.plot_cfg.factors.xlabel_time)
        ax.set_ylabel(self.plot_cfg.factors.ylabel_weight)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        for spine in ax.spines.values():
            spine.set_linewidth(self.plot_cfg.style.line_width)
        ax.legend()

        ax = axes[2]
        x = np.arange(len(features))
        width = 0.8 / rank
        for r in range(rank):
            ax.bar(x + r * width, feat_f[:, r], width=width, label=f"C{r + 1}")
        ax.set_xticks(x + width * (rank - 1) / 2)
        ax.set_xticklabels(features, rotation=45, ha="right")
        ax.set_title(self.plot_cfg.factors.title_feature)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        for spine in ax.spines.values():
            spine.set_linewidth(self.plot_cfg.style.line_width)
        ax.legend()

        fig.tight_layout()
        return fig, axes

    def plot_loading_boxes(self, load_df: pd.DataFrame) -> tuple:
        comps = sorted(load_df["component"].unique())
        fig_width = self.plot_cfg.loadings.fig_width_per_comp * len(comps)
        fig, axes = plt.subplots(
            1,
            len(comps),
            figsize=(fig_width, self.plot_cfg.loadings.fig_height),
            sharey=True,
        )
        if len(comps) == 1:
            axes = [axes]

        for ax, comp in zip(axes, comps):
            sub = load_df[load_df["component"] == comp]
            concs = [
                c
                for c in self.plot_cfg.plot_order
                if c in sub["concentration"].unique()
            ]
            data = [sub[sub["concentration"] == c]["loading"].values for c in concs]

            bp = ax.boxplot(
                data,
                positions=np.arange(len(concs)),
                widths=self.plot_cfg.style.box_width,
                patch_artist=True,
                showfliers=self.plot_cfg.style.show_fliers,
            )
            for patch, c in zip(bp["boxes"], concs):
                patch.set_facecolor(self.plot_cfg.color_map.get(c, "gray"))
                patch.set_alpha(self.plot_cfg.style.box_alpha)
                patch.set_edgecolor(self.plot_cfg.style.edge_color)
                patch.set_linewidth(self.plot_cfg.style.line_width)

            for i, vals in enumerate(data):
                if len(vals) == 0:
                    continue
                jitter = (np.random.rand(len(vals)) - 0.5) * self.plot_cfg.jitter.box
                ax.scatter(
                    np.full(len(vals), i) + jitter,
                    vals,
                    s=self.plot_cfg.style.point_size,
                    color=self.plot_cfg.style.edge_color,
                    alpha=self.plot_cfg.style.point_alpha,
                    zorder=10,
                    linewidths=self.plot_cfg.style.line_width,
                )

            try:
                groups = {c: data[i] for i, c in enumerate(concs)}
                stats = perform_tests(groups, self.control_group, paired=False)
            except Exception:
                stats = []

            if stats:
                y_vals = (
                    np.concatenate([v for v in data if len(v) > 0])
                    if any(len(v) for v in data)
                    else np.array([0])
                )
                y_min, y_max = float(np.nanmin(y_vals)), float(np.nanmax(y_vals))
                margin = 0.1 * (y_max - y_min if y_max != y_min else 1)
                base_y = y_max + margin * 1.2
                for idx, row in enumerate(stats):
                    conc_other = row["conc_other"]
                    if conc_other not in concs:
                        continue
                    x_pos = concs.index(conc_other)
                    ax.text(
                        x_pos,
                        base_y + idx * margin * 0.6,
                        p_to_star(row["p_value"]),
                        ha="center",
                        va="bottom",
                        fontsize=10,
                        fontweight="bold",
                    )
                ax.set_ylim(y_min - margin, base_y + margin * len(stats))

            ax.set_title(f"C{comp}")
            ax.set_xticks(np.arange(len(concs)))
            ax.set_xticklabels(
                [self.plot_cfg.dose_labels[c] for c in concs], rotation=45
            )
            ax.set_xlabel(self.plot_cfg.loadings.xlabel_dose)
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            for spine in ax.spines.values():
                spine.set_linewidth(self.plot_cfg.style.line_width)

        axes[0].set_ylabel(self.plot_cfg.loadings.ylabel_loading)
        fig.tight_layout()
        return fig, axes
