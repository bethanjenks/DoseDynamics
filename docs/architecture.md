# Architecture

## Pipeline flow

1. Optionally annotate arena corners and save to an HDF5 file.
2. Optionally assemble a combined DLC dataset from per-video H5 files.
3. Load DLC H5 file from config.
4. Extract a body part and metadata columns.
5. Add distance-from-wall feature.
6. Compute stop counts from full body-part data.
7. Bin features per animal (date + animal_id) and time window.
8. Build tensor and run TCA.
9. Plot factors and component loadings.
10. Optionally run speed-bin histogram analysis.
11. Optionally run speed/distance summary analysis.
12. Optionally run thigmotaxis analysis.
13. Optionally run dispersion analysis.
14. Optionally run arrest analysis.
15. Optionally run center crossings analysis.

## Extension points

- Add new analyses in `src/dosedynamics/analysis/` and wire them into `src/dosedynamics/pipeline.py`.
- Add new plotting routines in `src/dosedynamics/plotting/`.
- Add new config sections under `configs/`.
