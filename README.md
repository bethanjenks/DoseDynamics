# DoseDynamics

DoseDynamics is a research analysis toolbox for DeepLabCut (DLC)–based open-field experiments. It was developed to explore how pharmacological interventions influence free-moving mouse behaviour, both at the level of individual behavioural features and at the level of overall behavioural structure. The code brings together a collection of analysis routines that allow behaviour to be quantified, compared across dose conditions, and interpreted in a unified framework.

## Scientific motivation
Pharmacological manipulations can reshape behaviour in subtle and complex ways that are not always captured by a single metric. Changes in locomotion, exploration, stress-related behaviour, or spatial organisation often occur together and reflect broader shifts in behavioural state.

DoseDynamics was built to support this multiscale perspective by providing tools to:

	•	Quantify specific, interpretable behavioural features
	•	Combine multiple behavioural dimensions into multivariate analyses
	•	Compare behavioural patterns across dose conditions
	•	Explore how pharmacological perturbations reorganise behavioural activity and structure

Together, these analyses allow DoseDynamics to function as a practical toolbox for investigating how drugs modulate the dynamics and organisation of behaviour in open-field experiments, linking detailed behavioural measures with a broader, systems-level understanding of behavioural change.

## Installation

```bash
python -m venv .venv
. .venv/Scripts/activate
pip install -e .
```

## Quickstart

```bash
python -m dosedynamics run --config configs/default.yaml
```

Override config values inline:

```bash
python -m dosedynamics run --config configs/default.yaml \
  preprocessing.fps=30 \
  analysis.tca.rank=3
```

## Arena Corner Annotation

This step is used to manually define the four arena corners for each recording using an interactive OpenCV window. The user clicks the corners directly on a video frame, and the selected coordinates are saved to an HDF5 file.

These arena coordinates are then used to transform tracked positions into a common reference space, correcting for differences in camera angle, perspective distortion, or slight shifts in arena placement between recordings. This ensures that spatial analyses (e.g. center occupancy, wall distance, dispersion) are comparable across subjects and sessions. 

```bash
python -m dosedynamics arena-points --config configs/default.yaml
```

Set `arena_points.video_path`, `arena_points.time`, and `arena_points.output_h5` in the config or pass them as CLI args:

```bash
python -m dosedynamics arena-points --config configs/default.yaml \
  --video "C:\path\to\video.mp4" --time 60 --output "data/raw/arena_coords.h5"
```

## Dataset Assembly (make_dlc_dataframe)

This step consolidates multiple DeepLabCut output files into a single, analysis-ready dataset. It standardizes column formats, extracts and attaches experimental metadata (e.g. date, animal ID, dose condition), and writes a combined HDF5 file that serves as the main input for downstream analyses.

The goal of this stage is to transform raw DLC tracking outputs into a consistent, tidy dataframe structure that can be reused across different analysis modules without further manual preprocessing.

```bash
python -m dosedynamics assemble --config configs/default.yaml
```

All paths, filename patterns, and metadata parsing rules are in `dataset_build` in the config.

# Locomotion analysis
Locomotion metrics capture baseline activity and exploration dynamics in the open field and provide a first indication of how pharmacological interventions alter behavioural output. The analyses in this section quantify speed, distance travelled, and time-resolved movement patterns across dose conditions.

## Average Speed

Compute per-bin mean speeds and plot dose-vs-control histograms.

```bash
python -m dosedynamics speed-bins --config configs/default.yaml
```

Parameters for this analysis live under `analysis.speed_bins` in the config.

## Speed and Distance Travelled

Compute per-animal total distance and mean speed, with dose-vs-control summary plots.

```bash
python -m dosedynamics speed-distance --config configs/default.yaml
```

Parameters for this analysis live under `analysis.speed_distance` in the config.


## Dispersion (MEC)

Compute spatial dispersion using Minimum Enclosing Circle (MEC) radius distributions and plot dose-vs-control histograms. This metric reflects how widely an animal explores the arena, providing a measure of spatial spread and overall exploratory range under different pharmacological conditions.

```bash
python -m dosedynamics dispersion --config configs/default.yaml
```

Parameters for this analysis live under `analysis.dispersion` in the config.

# Measures of stress and anxiety 
In addition to locomotion and spatial spread, the toolbox includes behavioural measures that are commonly used in open-field paradigms to probe stress- and anxiety-related responses. Metrics such as thigmotaxis (wall-hugging behaviour), freezing and patterns of exploration provide indirect but widely adopted indicators of emotional or arousal state. Within DoseDynamics, these measures are used to examine how pharmacological interventions influence not only overall activity levels, but also spatial preference and risk-avoidance behaviours that are typically associated with stress or anxiety-like states.

## Thigmotaxis

Compute thigmotaxis indices and plot dose-vs-control summaries.

```bash
python -m dosedynamics thigmotaxis --config configs/default.yaml
```

Parameters for this analysis live under `analysis.thigmotaxis` in the config.


## Center Crossings

Compute center crossings with dose-vs-control summaries.

```bash
python -m dosedynamics center-crossings --config configs/default.yaml
```

Parameters for this analysis live under `analysis.center_crossings` in the config.


## Arrests

Compute behavioural arrest counts and durations with dose-vs-control summaries.

```bash
python -m dosedynamics arrests --config configs/default.yaml
```

Parameters for this analysis live under `analysis.arrest_analysis` in the config.

## Multivariate behavioural structure (TCA)

In addition to single-metric locomotion measures, DoseDynamics includes Tensor Component Analysis (TCA) as a way to explore behaviour at a more global level. TCA combines multiple behavioural features into a low-dimensional representation, making it possible to examine how different aspects of behaviour change together across dose conditions. This helps reveal coordinated, dose-dependent shifts in overall behavioural state that may not be apparent from any single metric alone, and provides a complementary, systems-level perspective on how pharmacological interventions reshape behaviour.

Run TCA with:
```bash
python -m dosedynamics tca --config configs/default.yaml
```
Parameters for this analysis live under `analysis.TCA` in the config.

## Configuration

All parameters are defined in YAML files under `configs/`. No experiment-specific values are hard-coded in Python. Use:

- `configs/default.yaml` for standard runs
- `configs/dev.yaml` for local or quick tests

CLI overrides use `key=value` syntax with dotted paths.

## Folder Structure

- `configs/` config files
- `data/raw/` input data (gitignored)
- `data/interim/` intermediate outputs (gitignored)
- `data/processed/` final outputs (gitignored)
- `reports/figures/` plots
- `src/dosedynamics/` package source
- `scripts/` runnable scripts
- `tests/` tests
- `docs/` documentation

## Adding New Analyses

1. Add a new module under `src/dosedynamics/analysis/`.
2. Define a config section in `configs/default.yaml`.
3. Wire the module into `dosedynamics/pipeline.py`.
4. Add plotting under `src/dosedynamics/plotting/`.

