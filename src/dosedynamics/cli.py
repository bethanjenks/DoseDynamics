import argparse
from typing import List

from dosedynamics.config import load_config
from dosedynamics.logging import setup_logging
from dosedynamics.pipeline import Pipeline


def _parse_args(argv: List[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="dosedynamics")
    sub = parser.add_subparsers(dest="command", required=True)

    def add_common(p: argparse.ArgumentParser) -> None:
        p.add_argument("--config", required=True, help="Path to config YAML")
        p.add_argument(
            "overrides",
            nargs="*",
            default=[],
            help="Config overrides as key=value",
        )

    add_common(sub.add_parser("run", help="Run full pipeline"))

    arena_parser = sub.add_parser("arena-points", help="Annotate arena corners")
    add_common(arena_parser)
    arena_parser.add_argument("--video", help="Path to the video file")
    arena_parser.add_argument("--time", help="Timestamp (seconds or HH:MM:SS(.ms))")
    arena_parser.add_argument("--output", help="Output HDF5 path")

    add_common(sub.add_parser("assemble", help="Assemble combined DLC dataset"))
    add_common(sub.add_parser("preprocess", help="Run preprocessing only"))
    add_common(sub.add_parser("analyze", help="Run analysis only"))
    add_common(sub.add_parser("plot", help="Run plotting only"))
    add_common(sub.add_parser("tca", help="Run TCA analysis + plots"))
    add_common(sub.add_parser("speed-bins", help="Run speed bin analysis"))
    add_common(sub.add_parser("speed-distance", help="Run speed and distance analysis"))
    add_common(sub.add_parser("thigmotaxis", help="Run thigmotaxis analysis"))
    add_common(sub.add_parser("dispersion", help="Run dispersion analysis"))
    add_common(sub.add_parser("arrests", help="Run arrest detection analysis"))
    add_common(sub.add_parser("center-crossings", help="Run center crossings analysis"))

    return parser.parse_args(args=argv)


def _arena_overrides(args: argparse.Namespace) -> List[str]:
    overrides = list(args.overrides)
    if args.video:
        overrides.append(f'arena_points.video_path="{args.video}"')
    if args.time:
        overrides.append(f'arena_points.time="{args.time}"')
    if args.output:
        overrides.append(f'arena_points.output_h5="{args.output}"')
    return overrides


def main(argv: List[str] | None = None) -> None:
    args = _parse_args(argv)
    overrides = (
        _arena_overrides(args) if args.command == "arena-points" else args.overrides
    )
    cfg = load_config(args.config, overrides)
    logger = setup_logging(cfg)

    pipeline = Pipeline(cfg, logger)

    if args.command == "run":
        pipeline.run()
    elif args.command == "arena-points":
        pipeline.run_arena_points()
    elif args.command == "assemble":
        pipeline.run_assemble()
    elif args.command == "preprocess":
        pipeline.run_preprocess()
    elif args.command == "analyze":
        pipeline.run_analyze()
    elif args.command == "plot":
        pipeline.run_plot()
    elif args.command == "tca":
        pipeline.run_tca()
    elif args.command == "speed-bins":
        pipeline.run_speed_bins()
    elif args.command == "speed-distance":
        pipeline.run_speed_distance()
    elif args.command == "thigmotaxis":
        pipeline.run_thigmotaxis()
    elif args.command == "dispersion":
        pipeline.run_dispersion()
    elif args.command == "arrests":
        pipeline.run_arrests()
    elif args.command == "center-crossings":
        pipeline.run_center_crossings()
    else:
        raise SystemExit(f"Unknown command: {args.command}")
