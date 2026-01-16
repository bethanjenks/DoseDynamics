from dosedynamics.config import ThigmotaxisConfig


def test_thigmotaxis_config_defaults():
    cfg = ThigmotaxisConfig(
        control_group="C",
        margin_frac=0.25,
        metric="thigmotaxis_index",
        area_normalize=False,
        save_figures=False,
        output_filename="thigmotaxis.png",
    )
    assert cfg.margin_frac == 0.25
