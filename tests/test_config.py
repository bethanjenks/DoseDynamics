import tempfile

import yaml

from dosedynamics.config import load_config


def test_load_config_with_overrides():
    data = {
        "project": {"name": "DoseDynamics"},
        "paths": {
            "base_dir": ".",
            "data_raw_dir": "data/raw",
            "data_interim_dir": "data/interim",
            "data_processed_dir": "data/processed",
            "reports_dir": "reports",
            "figures_dir": "reports/figures",
            "logs_dir": "reports/logs",
        },
        "logging": {"level": "INFO", "log_file": "pipeline.log"},
        "input": {
            "h5_path": "data/raw/combined.h5",
            "body_part": "spine_2",
            "meta_cols": ["date", "animal_id", "concentration", "administration"],
            "group_cols": ["date", "animal_id"],
        },
        "preprocessing": {
            "fps": 30,
            "cutoff_minutes": 30,
            "bin_seconds": 10,
            "likelihood_threshold": 0.8,
            "min_points": 5,
        },
        "arena": {"width_cm": 30.0, "length_cm": 40.0},
        "arrest": {"min_still_seconds": 2.0, "movement_threshold": 0.05},
        "analysis": {
            "tca": {
                "control_group": "C",
                "rank": 3,
                "max_iter": 100,
                "tol": 1.0e-6,
                "init": "svd",
                "normalize_factors": True,
                "stop_bin_seconds": 30,
                "features": {"base": ["speed_cms"], "extra": ["mec_radius"]},
                "fill_strategy": "median",
                "fill_value": 0.0,
                "l2_reg": 1.0e-6,
            },
            "speed_bins": {
                "control_group": "C",
                "bin_seconds": 10,
                "hist": {
                    "bins": 20,
                    "range_min": 0,
                    "range_max": 30,
                    "control_color": "gray",
                    "control_line_width": 1.6,
                    "conc_alpha": 0.55,
                    "conc_edge_color": "black",
                },
                "plot": {
                    "title_template": "Dose {dose} {dose_unit}",
                    "xlabel": "Bin mean speed (cm/s)",
                    "ylabel": "Count",
                    "fig_width_per_group": 4.4,
                    "fig_height": 4,
                },
                "save_figures": False,
                "output_filename": "speed_bins.png",
            },
            "speed_distance": {
                "control_group": "C",
                "save_figures": False,
                "metrics": {
                    "total_distance": {
                        "title": "Total Distance Travelled",
                        "ylabel": "Total Distance (cm)",
                        "output_filename": "total_distance.png",
                    },
                    "mean_speed": {
                        "title": "Mean Speed",
                        "ylabel": "Mean Speed (cm/s)",
                        "output_filename": "mean_speed.png",
                    },
                },
            },
            "thigmotaxis": {
                "control_group": "C",
                "margin_frac": 0.25,
                "metric": "thigmo_area_norm",
                "area_normalize": True,
                "save_figures": False,
                "output_filename": "thigmotaxis.png",
            },
            "dispersion": {
                "control_group": "C",
                "bin_seconds": 10,
                "save_figures": False,
                "output_filename": "dispersion.png",
                "plot_order": ["S", "L", "M", "H"],
                "hist": {
                    "bins": 30,
                    "y_max": 100,
                    "alpha_group": 0.8,
                    "alpha_control": 0.5,
                    "edge_color": "black",
                },
                "plot": {
                    "fig_width": 10,
                    "fig_height_per_row": 4,
                    "xlabel": "MEC radius (cm)",
                    "ylabel": "Count",
                    "title_template": "p = {p:.3g}, d = {d:.2f}",
                },
            },
            "arrest_analysis": {
                "control_group": "C",
                "paired": True,
                "save_figures": False,
                "stop_count": {
                    "title": "Behavioural Arrests",
                    "ylabel": "Stop Counts",
                    "output_filename": "arrest_counts.png",
                },
                "mean_duration": {
                    "title": "Mean Stop Duration",
                    "ylabel": "Mean Stop Duration (s)",
                    "output_filename": "arrest_duration.png",
                },
                "duration_hist": {
                    "bin_width": 0.5,
                    "xlim_max": 5,
                    "fig_width": 6,
                    "fig_height": 4,
                    "color": "steelblue",
                    "edge_color": "black",
                    "alpha": 0.8,
                    "xlabel": "Stop duration (s)",
                    "ylabel": "Count",
                    "title": "Stop duration distribution (all animals)",
                    "output_filename": "arrest_duration_hist.png",
                },
            },
            "center_crossings": {
                "control_group": "C",
                "inner_frac": 0.4,
                "save_figures": False,
                "output_filename": "center_crossings.png",
                "title": "Center crossings",
                "ylabel": "Count center crossings",
            },
        },
        "plotting": {
            "plot_order": ["C"],
            "dose_labels": {"C": "0"},
            "dose_unit": "ug/kg",
            "color_map": {"C": "gray"},
            "factors": {
                "fig_size": [10, 4],
                "title_mouse": "Mouse Loadings",
                "title_time": "Temporal Factors",
                "title_feature": "Feature Loadings",
                "xlabel_component": "Component",
                "ylabel_loading": "Loading",
                "xlabel_time": "Time (s)",
                "ylabel_weight": "Weight",
            },
            "loadings": {
                "fig_width_per_comp": 4.0,
                "fig_height": 4.0,
                "xlabel_dose": "Dose (ug/kg)",
                "ylabel_loading": "Mouse loading",
            },
            "jitter": {"mouse": 0.1, "box": 0.2},
            "style": {
                "point_size": 22,
                "point_alpha": 0.8,
                "box_width": 0.6,
                "box_alpha": 0.7,
                "edge_color": "black",
                "line_width": 1.2,
                "factor_line_width": 2.0,
                "show_fliers": False,
            },
            "save": {
                "enabled": False,
                "factors_filename": "f.png",
                "loadings_filename": "l.png",
            },
        },
        "dataset_build": {
            "input_dir": "data/raw/videos",
            "file_glob": "*.h5",
            "arena_coords_h5": "data/raw/arena.h5",
            "arena_video_col": "video_base",
            "arena_corner_index_col": "corner_idx",
            "arena_x_col": "x",
            "arena_y_col": "y",
            "output_h5": "data/interim/combined.h5",
            "output_key": "df",
            "output_mode": "a",
            "output_format": "table",
            "append": True,
            "video_name": {"split_token": "DLC", "extension": ".mp4"},
            "metadata_fields": [
                {
                    "name": "animal_id",
                    "source": "filename",
                    "pattern": "_(?P<animal_id>[^_]+)_",
                    "transform": "none",
                }
            ],
            "administration": {"default": "unknown", "map": {"catheter": [], "IP": []}},
        },
        "arena_points": {
            "video_path": "data/raw/videos/example.mp4",
            "time": "60",
            "output_h5": "data/raw/arena_coords.h5",
            "h5_key": "corners",
            "window_name": "Arena Annotator",
            "click_order": ["TL", "TR", "BR", "BL"],
            "max_display_width": 1280,
            "max_display_height": 720,
        },
        "output": {"save_processed": False, "processed_filename": "bins.parquet"},
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.safe_dump(data, f)
        path = f.name

    cfg = load_config(path, ["analysis.tca.rank=4", "preprocessing.fps=25"])
    assert cfg.analysis.tca.rank == 4
    assert cfg.preprocessing.fps == 25
