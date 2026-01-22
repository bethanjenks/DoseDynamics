# DoseDynamics

DoseDynamics is an analysis pipeline for DeepLabCut (DLC)–based open-field experiments, designed to quantify how pharmacological interventions reshape free-moving mouse behaviour. It combines interpretable behavioural metrics with multivariate modelling to understand how drug dose modulates both specific actions and the overall structure of behavioural activity.

## Scientific motivation
Pharmacological interventions can alter behaviour in complex ways that are not
fully captured by any single metric. Changes in activity, exploration, or
spatial preference often emerge alongside shifts in global behavioural structure.

DoseDynamics was built to support this multiscale view by enabling:

- Quantification of specific, interpretable behavioural features  
- Integration of multiple behavioural dimensions into multivariate models  
- Comparison of behavioural structure across dose conditions  
- Systematic evaluation of how pharmacological perturbations reshape activity
  and behavioural state

Together, these components allow DoseDynamics to be used not only as an
analysis pipeline, but as a framework for investigating how drugs modulate
the dynamics and organisation of behaviour.

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

Use the arena annotation step to click the 4 corners of the arena and save them to an HDF5 file.

```bash
python -m dosedynamics arena-points --config configs/default.yaml
```

Set `arena_points.video_path`, `arena_points.time`, and `arena_points.output_h5` in the config or pass them as CLI args:

```bash
python -m dosedynamics arena-points --config configs/default.yaml \
  --video "C:\path\to\video.mp4" --time 60 --output "data/raw/arena_coords.h5"
```

## Dataset Assembly (make_dlc_dataframe)

Use the assembly step to normalize DLC H5 files, add metadata, and write a combined H5.

```bash
python -m dosedynamics assemble --config configs/default.yaml
```

All paths, filename patterns, and metadata parsing rules are in `dataset_build` in the config.

# Locomotion analysis

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

Compute dispersion via MEC radius distributions and plot dose-vs-control histograms.

```bash
python -m dosedynamics dispersion --config configs/default.yaml
```

Parameters for this analysis live under `analysis.dispersion` in the config.

# Measures of stress 

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

In addition to single-metric locomotion measures, DoseDynamics supports Tensor Component Analysis (TCA) to capture the global structure of behaviour across multiple features. TCA integrates several behavioural metrics into a low-dimensional representation, allowing coordinated, dose-dependent changes in overall behavioural state to be identified. This provides a systems-level view of how pharmacological interventions reshape behaviour, complementing the more interpretable single-feature analyses.

Run TCA with:
```bash
python -m dosedynamics tca --config configs/default.yaml
```

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

## Reproducing Results

- Use a config file with fixed parameters and paths.
- Run the pipeline with `python -m dosedynamics run --config <config>`.
- Outputs are written under `data/processed/` and `reports/figures/`.
