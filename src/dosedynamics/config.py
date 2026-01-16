from __future__ import annotations

from typing import Any, Dict, List

import yaml
from pydantic import BaseModel


class ProjectConfig(BaseModel):
    name: str


class PathsConfig(BaseModel):
    base_dir: str
    data_raw_dir: str
    data_interim_dir: str
    data_processed_dir: str
    reports_dir: str
    figures_dir: str
    logs_dir: str


class LoggingConfig(BaseModel):
    level: str
    log_file: str


class InputConfig(BaseModel):
    h5_path: str
    body_part: str
    meta_cols: List[str]
    group_cols: List[str]


class PreprocessingConfig(BaseModel):
    fps: float
    cutoff_minutes: float
    bin_seconds: float
    likelihood_threshold: float
    min_points: int


class ArenaConfig(BaseModel):
    width_cm: float
    length_cm: float


class ArrestConfig(BaseModel):
    min_still_seconds: float
    movement_threshold: float


class TCAFeatureConfig(BaseModel):
    base: List[str]
    extra: List[str]


class TCAConfig(BaseModel):
    control_group: str
    rank: int
    max_iter: int
    tol: float
    init: str
    normalize_factors: bool
    stop_bin_seconds: float
    features: TCAFeatureConfig
    fill_strategy: str
    fill_value: float
    l2_reg: float


class SpeedBinsHistogramConfig(BaseModel):
    bins: int
    range_min: float
    range_max: float
    control_color: str
    control_line_width: float
    conc_alpha: float
    conc_edge_color: str


class SpeedBinsPlotConfig(BaseModel):
    title_template: str
    xlabel: str
    ylabel: str
    fig_width_per_group: float
    fig_height: float


class SpeedBinsConfig(BaseModel):
    control_group: str
    bin_seconds: float
    hist: SpeedBinsHistogramConfig
    plot: SpeedBinsPlotConfig
    save_figures: bool
    output_filename: str


class SpeedDistanceMetricConfig(BaseModel):
    title: str
    ylabel: str
    output_filename: str


class SpeedDistanceConfig(BaseModel):
    control_group: str
    save_figures: bool
    metrics: Dict[str, SpeedDistanceMetricConfig]


class ThigmotaxisConfig(BaseModel):
    control_group: str
    margin_frac: float
    metric: str
    area_normalize: bool
    save_figures: bool
    output_filename: str


class DispersionHistogramConfig(BaseModel):
    bins: int
    y_max: float
    alpha_group: float
    alpha_control: float
    edge_color: str


class DispersionPlotConfig(BaseModel):
    fig_width: float
    fig_height_per_row: float
    xlabel: str
    ylabel: str
    title_template: str


class DispersionConfig(BaseModel):
    control_group: str
    bin_seconds: float
    save_figures: bool
    output_filename: str
    plot_order: List[str]
    hist: DispersionHistogramConfig
    plot: DispersionPlotConfig


class ArrestMetricConfig(BaseModel):
    title: str
    ylabel: str
    output_filename: str


class ArrestHistogramConfig(BaseModel):
    bin_width: float
    xlim_max: float
    fig_width: float
    fig_height: float
    color: str
    edge_color: str
    alpha: float
    xlabel: str
    ylabel: str
    title: str
    output_filename: str


class ArrestAnalysisConfig(BaseModel):
    control_group: str
    paired: bool
    save_figures: bool
    stop_count: ArrestMetricConfig
    mean_duration: ArrestMetricConfig
    duration_hist: ArrestHistogramConfig


class CenterCrossingsConfig(BaseModel):
    control_group: str
    inner_frac: float
    save_figures: bool
    output_filename: str
    title: str
    ylabel: str


class AnalysisConfig(BaseModel):
    tca: TCAConfig
    speed_bins: SpeedBinsConfig
    speed_distance: SpeedDistanceConfig
    thigmotaxis: ThigmotaxisConfig
    dispersion: DispersionConfig
    arrest_analysis: ArrestAnalysisConfig
    center_crossings: CenterCrossingsConfig


class PlotFactorsConfig(BaseModel):
    fig_size: List[float]
    title_mouse: str
    title_time: str
    title_feature: str
    xlabel_component: str
    ylabel_loading: str
    xlabel_time: str
    ylabel_weight: str


class PlotLoadingsConfig(BaseModel):
    fig_width_per_comp: float
    fig_height: float
    xlabel_dose: str
    ylabel_loading: str


class PlotJitterConfig(BaseModel):
    mouse: float
    box: float


class PlotStyleConfig(BaseModel):
    point_size: float
    point_alpha: float
    box_width: float
    box_alpha: float
    edge_color: str
    line_width: float
    factor_line_width: float
    show_fliers: bool


class PlotSaveConfig(BaseModel):
    enabled: bool
    factors_filename: str
    loadings_filename: str


class PlottingConfig(BaseModel):
    plot_order: List[str]
    dose_labels: Dict[str, str]
    dose_unit: str
    color_map: Dict[str, str]
    factors: PlotFactorsConfig
    loadings: PlotLoadingsConfig
    jitter: PlotJitterConfig
    style: PlotStyleConfig
    save: PlotSaveConfig


class MetadataFieldConfig(BaseModel):
    name: str
    source: str
    pattern: str
    transform: str | None = None


class VideoNameConfig(BaseModel):
    split_token: str
    extension: str


class AdministrationConfig(BaseModel):
    default: str
    map: Dict[str, List[str]]


class DatasetBuildConfig(BaseModel):
    input_dir: str
    file_glob: str
    arena_coords_h5: str
    arena_video_col: str
    arena_corner_index_col: str
    arena_x_col: str
    arena_y_col: str
    output_h5: str
    output_key: str
    output_mode: str
    output_format: str
    append: bool
    video_name: VideoNameConfig
    metadata_fields: List[MetadataFieldConfig]
    administration: AdministrationConfig


class ArenaPointsConfig(BaseModel):
    video_path: str
    time: str
    output_h5: str
    h5_key: str
    window_name: str
    click_order: List[str]
    max_display_width: int
    max_display_height: int


class OutputConfig(BaseModel):
    save_processed: bool
    processed_filename: str


class Config(BaseModel):
    project: ProjectConfig
    paths: PathsConfig
    logging: LoggingConfig
    input: InputConfig
    preprocessing: PreprocessingConfig
    arena: ArenaConfig
    arrest: ArrestConfig
    analysis: AnalysisConfig
    plotting: PlottingConfig
    dataset_build: DatasetBuildConfig
    arena_points: ArenaPointsConfig
    output: OutputConfig


def _set_nested(data: Dict[str, Any], keys: List[str], value: Any) -> None:
    cur = data
    for key in keys[:-1]:
        if key not in cur or not isinstance(cur[key], dict):
            cur[key] = {}
        cur = cur[key]
    cur[keys[-1]] = value


def apply_overrides(data: Dict[str, Any], overrides: List[str]) -> Dict[str, Any]:
    out = dict(data)
    for item in overrides:
        if "=" not in item:
            raise ValueError(f"Invalid override '{item}', expected key=value")
        key, raw = item.split("=", 1)
        value = yaml.safe_load(raw)
        _set_nested(out, key.split("."), value)
    return out


def load_config(path: str, overrides: List[str]) -> Config:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    data = apply_overrides(data, overrides)
    return Config.model_validate(data)
