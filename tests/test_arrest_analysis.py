from dosedynamics.config import ArrestAnalysisConfig, ArrestHistogramConfig, ArrestMetricConfig


def test_arrest_analysis_config():
    cfg = ArrestAnalysisConfig(
        control_group="C",
        paired=True,
        save_figures=False,
        stop_count=ArrestMetricConfig(
            title="Behavioural Arrests",
            ylabel="Stop Counts",
            output_filename="arrest_counts.png",
        ),
        mean_duration=ArrestMetricConfig(
            title="Mean Stop Duration",
            ylabel="Mean Stop Duration (s)",
            output_filename="arrest_duration.png",
        ),
        duration_hist=ArrestHistogramConfig(
            bin_width=0.5,
            xlim_max=5,
            fig_width=6,
            fig_height=4,
            color="steelblue",
            edge_color="black",
            alpha=0.8,
            xlabel="Stop duration (s)",
            ylabel="Count",
            title="Stop duration distribution (all animals)",
            output_filename="arrest_duration_hist.png",
        ),
    )
    assert cfg.paired is True
