from dosedynamics.config import DispersionConfig


def test_dispersion_config_defaults():
    cfg = DispersionConfig(
        control_group="C",
        bin_seconds=10,
        save_figures=False,
        output_filename="dispersion.png",
        plot_order=["S", "L"],
        hist={
            "bins": 30,
            "y_max": 100,
            "alpha_group": 0.8,
            "alpha_control": 0.5,
            "edge_color": "black",
        },
        plot={
            "fig_width": 10,
            "fig_height_per_row": 4,
            "xlabel": "MEC radius (cm)",
            "ylabel": "Count",
            "title_template": "p = {p:.3g}, d = {d:.2f}",
        },
    )
    assert cfg.hist.bins == 30
