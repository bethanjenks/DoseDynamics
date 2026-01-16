from __future__ import annotations

import math
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from dosedynamics.analysis.stats import get_cohens_d
from dosedynamics.config import DispersionConfig, PlottingConfig


class DispersionPlotter:
    def __init__(self, plot_cfg: PlottingConfig, disp_cfg: DispersionConfig) -> None:
        self.plot_cfg = plot_cfg
        self.disp_cfg = disp_cfg

    def plot_distributions(
        self,
        per_bin: pd.DataFrame,
        stats: list[dict],
    ) -> Tuple:
        control = self.disp_cfg.control_group
        plot_order = self.disp_cfg.plot_order
        groups = {
            conc: g["radius"].values for conc, g in per_bin.groupby("concentration")
        }

        concs = [c for c in plot_order if c in groups]
        n = len(concs)
        if n == 0:
            raise ValueError("No concentration groups for dispersion plot")

        cols = 2
        rows = int(math.ceil(n / cols))

        fig, axes = plt.subplots(
            rows,
            cols,
            figsize=(self.disp_cfg.plot.fig_width, self.disp_cfg.plot.fig_height_per_row * rows),
        )
        axes = np.atleast_1d(axes).ravel()

        all_radii = per_bin["radius"].values
        bin_edges = np.histogram_bin_edges(all_radii, bins=self.disp_cfg.hist.bins)
        xmin = float(np.nanmin(all_radii))
        xmax = float(np.nanmax(all_radii))

        for ax, conc in zip(axes, concs):
            ax.hist(
                groups[conc],
                bins=bin_edges,
                color=self.plot_cfg.color_map.get(conc, "gray"),
                edgecolor=self.disp_cfg.hist.edge_color,
                alpha=self.disp_cfg.hist.alpha_group,
                label=f"{self.plot_cfg.dose_labels.get(conc, conc)} {self.plot_cfg.dose_unit}",
            )
            ax.hist(
                groups[control],
                bins=bin_edges,
                color=self.plot_cfg.color_map.get(control, "gray"),
                edgecolor=self.disp_cfg.hist.edge_color,
                alpha=self.disp_cfg.hist.alpha_control,
                label=f"{self.plot_cfg.dose_labels.get(control, control)} {self.plot_cfg.dose_unit} (control)",
            )

            p_row = next((r for r in stats if r.get("conc_other") == conc), None)
            p_val = p_row["p_value"] if p_row else np.nan
            d_val = get_cohens_d(groups[conc], groups[control])

            ax.set_title(
                self.disp_cfg.plot.title_template.format(p=p_val, d=d_val),
                fontsize=13,
            )
            ax.set_xlabel(self.disp_cfg.plot.xlabel, fontsize=12)
            ax.set_ylabel(self.disp_cfg.plot.ylabel, fontsize=12)
            ax.set_ylim(0, self.disp_cfg.hist.y_max)
            ax.set_xlim(xmin - 0.5, xmax + 0.5)
            ax.grid(False)
            ax.tick_params(
                axis="both",
                which="both",
                direction="out",
                length=6,
                width=self.plot_cfg.style.line_width,
                labelsize=11,
            )
            for spine in ax.spines.values():
                spine.set_visible(True)
                spine.set_linewidth(self.plot_cfg.style.line_width)
            ax.legend(fontsize=10)

        for ax in axes[len(concs):]:
            ax.axis("off")

        fig.tight_layout()
        return fig, axes
