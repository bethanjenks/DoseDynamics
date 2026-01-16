from dosedynamics.config import CenterCrossingsConfig


def test_center_crossings_config():
    cfg = CenterCrossingsConfig(
        control_group="C",
        inner_frac=0.4,
        save_figures=False,
        output_filename="center_crossings.png",
        title="Center crossings",
        ylabel="Count center crossings",
    )
    assert cfg.inner_frac == 0.4
