from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd

from dosedynamics.analysis.stats import p_to_star
from dosedynamics.config import PlottingConfig, SpeedBinsConfig


class SpeedBinsPlotter:
    def __init__(
        self,
        plot_cfg: PlottingConfig,
        speed_cfg: SpeedBinsConfig,
    ) -> None:
        self.plot_cfg = plot_cfg
        self.speed_cfg = speed_cfg

    def plot_distribution(
        self,
        bin_speeds: pd.DataFrame,
        stats: list[dict],
    ) -> tuple:
        concs = [
            c
            for c in self.plot_cfg.plot_order
            if c in bin_speeds["concentration"].unique()
        ]
        control_vals = bin_speeds.loc[
            bin_speeds["concentration"] == self.speed_cfg.control_group, "bin_speed"
        ].values
        if len(control_vals) == 0:
            raise ValueError("No control data found for speed bin plot")

        fig, axes = plt.subplots(
            1,
            len(concs),
            figsize=(
                self.speed_cfg.plot.fig_width_per_group * len(concs),
                self.speed_cfg.plot.fig_height,
            ),
            sharey=True,
        )
        if len(concs) == 1:
            axes = [axes]

        bins = self.speed_cfg.hist.bins
        hist_range = (self.speed_cfg.hist.range_min, self.speed_cfg.hist.range_max)

        for ax, conc in zip(axes, concs):
            conc_vals = bin_speeds.loc[
                bin_speeds["concentration"] == conc, "bin_speed"
            ].values

            ax.hist(
                control_vals,
                bins=bins,
                range=hist_range,
                density=False,
                histtype="step",
                color=self.speed_cfg.hist.control_color,
                linewidth=self.speed_cfg.hist.control_line_width,
                label=f"Control ({len(control_vals)})",
            )
            ax.hist(
                conc_vals,
                bins=bins,
                range=hist_range,
                density=False,
                histtype="bar",
                color=self.plot_cfg.color_map.get(conc, "gray"),
                alpha=self.speed_cfg.hist.conc_alpha,
                edgecolor=self.speed_cfg.hist.conc_edge_color,
                label=f"{self.plot_cfg.dose_labels.get(conc, conc)} ({len(conc_vals)})",
            )

            dose = self.plot_cfg.dose_labels.get(conc, conc)
            ax.set_title(
                self.speed_cfg.plot.title_template.format(
                    dose=dose, dose_unit=self.plot_cfg.dose_unit
                )
            )
            ax.set_xlabel(self.speed_cfg.plot.xlabel)
            ax.set_ylabel(self.speed_cfg.plot.ylabel)
            ax.set_xlim(hist_range)
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.legend(fontsize=9, frameon=False)

            row = next((r for r in stats if r.get("conc_other") == conc), None)
            if row:
                label = p_to_star(row["p_value"])
                ax.text(
                    0.95,
                    0.9,
                    label,
                    ha="right",
                    va="top",
                    transform=ax.transAxes,
                    fontsize=12,
                    fontweight="bold",
                )

        fig.tight_layout()
        return fig, axes
