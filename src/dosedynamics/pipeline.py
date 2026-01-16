from __future__ import annotations

from dosedynamics.analysis.arrest_analysis import ArrestAnalysis
from dosedynamics.analysis.center_crossings import CenterCrossingsAnalysis
from dosedynamics.analysis.dispersion import DispersionAnalysis
from dosedynamics.analysis.speed_bins import SpeedBinsAnalysis
from dosedynamics.analysis.speed_distance import SpeedDistanceAnalysis
from dosedynamics.analysis.tca_per_animal import TCAPerAnimalAnalysis
from dosedynamics.analysis.thigmotaxis import ThigmotaxisAnalysis
from dosedynamics.config import Config
from dosedynamics.io.savers import save_figure
from dosedynamics.plotting.arrest import ArrestPlotter
from dosedynamics.plotting.center_crossings import CenterCrossingsPlotter
from dosedynamics.plotting.dispersion import DispersionPlotter
from dosedynamics.plotting.speed_bins import SpeedBinsPlotter
from dosedynamics.plotting.speed_distance import SpeedDistancePlotter
from dosedynamics.plotting.tca import TCAPlotter
from dosedynamics.plotting.thigmotaxis import ThigmotaxisPlotter
from dosedynamics.preprocessing.assemble import DLCCombinedBuilder
from dosedynamics.preprocessing.arena_points import ArenaPointsAnnotator
from dosedynamics.utils.paths import PathManager


class Pipeline:
    def __init__(self, cfg: Config, logger) -> None:
        self.cfg = cfg
        self.logger = logger
        self.paths = PathManager(cfg)
        self.analysis = TCAPerAnimalAnalysis(cfg, logger)
        self.speed_bins = SpeedBinsAnalysis(cfg, logger)
        self.speed_distance = SpeedDistanceAnalysis(cfg, logger)
        self.thigmotaxis = ThigmotaxisAnalysis(cfg, logger)
        self.dispersion = DispersionAnalysis(cfg, logger)
        self.center_crossings = CenterCrossingsAnalysis(cfg, logger)
        self.arrests = ArrestAnalysis(cfg, logger)
        self.assembler = DLCCombinedBuilder(cfg, logger)
        self.arena_points = ArenaPointsAnnotator(cfg, logger)
        self.plotter = TCAPlotter(
            cfg.plotting,
            bin_seconds=cfg.preprocessing.bin_seconds,
            control_group=cfg.analysis.tca.control_group,
        )
        self.speed_bins_plotter = SpeedBinsPlotter(cfg.plotting, cfg.analysis.speed_bins)
        self.speed_distance_plotter = SpeedDistancePlotter(
            cfg.plotting, cfg.analysis.speed_distance
        )
        self.thigmotaxis_plotter = ThigmotaxisPlotter(cfg.plotting, cfg.analysis.thigmotaxis)
        self.dispersion_plotter = DispersionPlotter(cfg.plotting, cfg.analysis.dispersion)
        self.center_crossings_plotter = CenterCrossingsPlotter(
            cfg.plotting, cfg.analysis.center_crossings
        )
        self.arrest_plotter = ArrestPlotter(cfg.plotting, cfg.analysis.arrest_analysis)

    def run_arena_points(self) -> None:
        self.arena_points.run()

    def run_assemble(self) -> None:
        self.assembler.run()

    def run_preprocess(self) -> None:
        self.analysis.prepare_bin_df()

    def run_analyze(self):
        return self.analysis.run()

    def run_speed_bins(self) -> None:
        results = self.speed_bins.run()
        fig, _ = self.speed_bins_plotter.plot_distribution(results.bin_speeds, results.stats)
        if self.cfg.analysis.speed_bins.save_figures:
            figures_dir = self.paths.figures_dir()
            save_figure(fig, figures_dir / self.cfg.analysis.speed_bins.output_filename)
            self.logger.info("Saved speed bin figure to %s", figures_dir)

    def run_speed_distance(self) -> None:
        results = self.speed_distance.run()
        for metric, stats in results.stats_by_metric.items():
            fig, _ = self.speed_distance_plotter.plot_metric(
                results.per_group, metric, stats
            )
            if self.cfg.analysis.speed_distance.save_figures:
                output_name = self.cfg.analysis.speed_distance.metrics[metric].output_filename
                figures_dir = self.paths.figures_dir()
                save_figure(fig, figures_dir / output_name)
                self.logger.info("Saved %s plot to %s", metric, figures_dir)

    def run_thigmotaxis(self) -> None:
        results = self.thigmotaxis.run()
        fig, _ = self.thigmotaxis_plotter.plot_metric(results.per_group, results.stats)
        if self.cfg.analysis.thigmotaxis.save_figures:
            figures_dir = self.paths.figures_dir()
            save_figure(fig, figures_dir / self.cfg.analysis.thigmotaxis.output_filename)
            self.logger.info("Saved thigmotaxis plot to %s", figures_dir)

    def run_dispersion(self) -> None:
        results = self.dispersion.run()
        fig, _ = self.dispersion_plotter.plot_distributions(results.per_bin, results.stats)
        if self.cfg.analysis.dispersion.save_figures:
            figures_dir = self.paths.figures_dir()
            save_figure(fig, figures_dir / self.cfg.analysis.dispersion.output_filename)
            self.logger.info("Saved dispersion plot to %s", figures_dir)

    def run_center_crossings(self) -> None:
        results = self.center_crossings.run()
        fig, _ = self.center_crossings_plotter.plot_crossings(
            results.per_group, results.stats
        )
        if self.cfg.analysis.center_crossings.save_figures:
            figures_dir = self.paths.figures_dir()
            save_figure(fig, figures_dir / self.cfg.analysis.center_crossings.output_filename)
            self.logger.info("Saved center crossings plot to %s", figures_dir)

    def run_arrests(self) -> None:
        results = self.arrests.run()
        if results.arrests.empty:
            self.logger.info("No arrests detected; skipping plots")
            return
        fig_counts, _ = self.arrest_plotter.plot_stop_counts(
            results.stops_per_session, results.stats_stops
        )
        fig_duration, _ = self.arrest_plotter.plot_mean_duration(
            results.mean_duration_per_session, results.stats_duration
        )
        fig_hist, _ = self.arrest_plotter.plot_duration_histogram(results.arrests)
        if self.cfg.analysis.arrest_analysis.save_figures:
            figures_dir = self.paths.figures_dir()
            save_figure(fig_counts, figures_dir / self.cfg.analysis.arrest_analysis.stop_count.output_filename)
            save_figure(fig_duration, figures_dir / self.cfg.analysis.arrest_analysis.mean_duration.output_filename)
            save_figure(fig_hist, figures_dir / self.cfg.analysis.arrest_analysis.duration_hist.output_filename)
            self.logger.info("Saved arrest plots to %s", figures_dir)

    def run_tca(self) -> None:
        self.run_plot()

    def run_plot(self) -> None:
        results = self.analysis.run()

        fig_factors, _ = self.plotter.plot_factors(
            results.factors,
            results.meta,
            results.features,
            results.n_bins,
        )
        load_df = self.analysis.build_loading_df(results.factors, results.meta)
        fig_loadings, _ = self.plotter.plot_loading_boxes(load_df)

        if self.cfg.plotting.save.enabled:
            figures_dir = self.paths.figures_dir()
            save_figure(fig_factors, figures_dir / self.cfg.plotting.save.factors_filename)
            save_figure(fig_loadings, figures_dir / self.cfg.plotting.save.loadings_filename)
            self.logger.info("Saved figures to %s", figures_dir)

    def run(self) -> None:
        self.run_preprocess()
        self.run_analyze()
        self.run_plot()
