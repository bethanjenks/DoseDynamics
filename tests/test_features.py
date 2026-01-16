from dosedynamics.analysis.features import build_feature_names


def test_build_feature_names():
    names = build_feature_names(["speed_cms", "dist_from_wall"], ["mec_radius"])
    assert "speed_cms" in names
    assert "dist_from_wall" in names
    assert "mec_radius" in names
