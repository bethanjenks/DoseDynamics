from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from dosedynamics.analysis.stats import p_to_star
from dosedynamics.config import ArrestAnalysisConfig, PlottingConfig


class ArrestPlotter:
    def __init__(
        self, plot_cfg: PlottingConfig, arrest_cfg: ArrestAnalysisConfig
    ) -> None:
        self.plot_cfg = plot_cfg
        self.arrest_cfg = arrest_cfg

    def plot_stop_counts(
        self, stops_per_session: pd.DataFrame, stats: list[dict]
    ) -> tuple:
        concs = [
            c
            for c in self.plot_cfg.plot_order
            if c in stops_per_session["concentration"].unique()
        ]
        x = np.arange(len(concs))

        grouped = stops_per_session.groupby("concentration")["n_stops"]
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
            vals = stops_per_session[stops_per_session["concentration"] == conc][
                "n_stops"
            ].values
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
        ax.set_ylabel(self.arrest_cfg.stop_count.ylabel, fontsize=12)
        ax.set_title(self.arrest_cfg.stop_count.title, fontsize=13)

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

    def plot_mean_duration(
        self, mean_duration: pd.DataFrame, stats: list[dict]
    ) -> tuple:
        concs = [
            c
            for c in self.plot_cfg.plot_order
            if c in mean_duration["concentration"].unique()
        ]
        x = np.arange(len(concs))

        grouped = mean_duration.groupby("concentration")["mean_stop_duration_s"]
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
            vals = mean_duration[mean_duration["concentration"] == conc][
                "mean_stop_duration_s"
            ].values
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
        ax.set_ylabel(self.arrest_cfg.mean_duration.ylabel, fontsize=12)
        ax.set_title(self.arrest_cfg.mean_duration.title, fontsize=13)

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

    def plot_duration_histogram(self, arrests: pd.DataFrame) -> tuple:
        durations = (
            arrests["duration_s"].dropna()
            if not arrests.empty
            else pd.Series(dtype=float)
        )
        if durations.empty:
            raise ValueError("No arrests detected; cannot plot duration histogram")

        max_dur = float(durations.max())
        bin_width = self.arrest_cfg.duration_hist.bin_width
        bins = np.arange(0, max_dur + bin_width + 1e-9, bin_width)

        fig, ax = plt.subplots(
            figsize=(
                self.arrest_cfg.duration_hist.fig_width,
                self.arrest_cfg.duration_hist.fig_height,
            )
        )
        ax.hist(
            durations,
            bins=bins,
            color=self.arrest_cfg.duration_hist.color,
            edgecolor=self.arrest_cfg.duration_hist.edge_color,
            alpha=self.arrest_cfg.duration_hist.alpha,
        )
        ax.set_xlabel(self.arrest_cfg.duration_hist.xlabel)
        ax.set_ylabel(self.arrest_cfg.duration_hist.ylabel)
        ax.set_title(self.arrest_cfg.duration_hist.title)
        ax.set_xlim(0, self.arrest_cfg.duration_hist.xlim_max)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        fig.tight_layout()
        return fig, ax
