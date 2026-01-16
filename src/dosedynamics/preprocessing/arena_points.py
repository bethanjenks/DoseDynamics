from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys
from typing import List

import cv2
import pandas as pd

from dosedynamics.config import Config
from dosedynamics.utils.paths import PathManager


@dataclass
class FrameInfo:
    fps: float
    width: int
    height: int
    frame_index: int
    timestamp_seconds: float


class ArenaPointsAnnotator:
    def __init__(self, cfg: Config, logger) -> None:
        self.cfg = cfg
        self.logger = logger
        self.paths = PathManager(cfg)

    def parse_time(self, s: str) -> float:
        if ":" not in s:
            return float(s)

        parts = s.split(":")
        if len(parts) == 2:
            h, m, sec = 0, int(parts[0]), float(parts[1])
        elif len(parts) == 3:
            h, m, sec = int(parts[0]), int(parts[1]), float(parts[2])
        else:
            raise ValueError("Invalid time format")

        return h * 3600 + m * 60 + sec

    def _ensure_table(self, h5_path: Path) -> None:
        if h5_path.exists():
            return
        cols = [
            "video_abs",
            "video_base",
            "frame_index",
            "timestamp_seconds",
            "width",
            "height",
            "corner_idx",
            "x",
            "y",
        ]
        pd.DataFrame(columns=cols).to_hdf(
            h5_path,
            self.cfg.arena_points.h5_key,
            format="table",
            data_columns=True,
        )

    def _load_frame(self, video_path: Path) -> tuple:
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise RuntimeError("Cannot open video")
        fps = cap.get(cv2.CAP_PROP_FPS) or 0
        if fps <= 0:
            raise RuntimeError("FPS unknown")
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        t = self.parse_time(self.cfg.arena_points.time)
        idx = max(0, int(round(t * fps)))

        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ok, frame = cap.read()
        cap.release()
        if not ok:
            raise RuntimeError("Cannot read frame at that time")

        info = FrameInfo(
            fps=fps,
            width=width,
            height=height,
            frame_index=idx,
            timestamp_seconds=t,
        )
        return frame, info

    def _write_points(self, pts: List[tuple], frame_info: FrameInfo, video_path: Path) -> None:
        self._ensure_table(self.paths.resolve(self.cfg.arena_points.output_h5))
        df = pd.DataFrame(
            {
                "video_abs": [str(video_path.resolve())] * len(pts),
                "video_base": [video_path.name] * len(pts),
                "frame_index": [frame_info.frame_index] * len(pts),
                "timestamp_seconds": [frame_info.timestamp_seconds] * len(pts),
                "width": [frame_info.width] * len(pts),
                "height": [frame_info.height] * len(pts),
                "corner_idx": list(range(1, len(pts) + 1)),
                "x": [p[0] for p in pts],
                "y": [p[1] for p in pts],
            }
        )
        with pd.HDFStore(self.paths.resolve(self.cfg.arena_points.output_h5)) as store:
            store.append(self.cfg.arena_points.h5_key, df, format="table", data_columns=True)

    def run(self) -> None:
        video_path = self.paths.resolve(self.cfg.arena_points.video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"Video not found: {video_path}")

        frame, frame_info = self._load_frame(video_path)
        pts: List[tuple] = []

        click_count = len(self.cfg.arena_points.click_order)
        window_name = self.cfg.arena_points.window_name

        def hud(img, text, y):
            cv2.putText(img, text, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 3)
            cv2.putText(img, text, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

        def redraw():
            disp[:] = frame
            for i, (px, py) in enumerate(pts):
                cv2.circle(disp, (px, py), 5, (0, 255, 255), -1)
                cv2.putText(
                    disp,
                    str(i + 1),
                    (px + 6, py - 6),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 255),
                    2,
                )
                if i > 0:
                    cv2.line(disp, pts[i - 1], pts[i], (0, 255, 0), 2)
            if len(pts) == click_count:
                cv2.line(disp, pts[-1], pts[0], (0, 255, 0), 2)

            hud(
                disp,
                f"{video_path.name} | time {frame_info.timestamp_seconds:.3f}s | frame {frame_info.frame_index}",
                24,
            )
            order_label = " -> ".join(self.cfg.arena_points.click_order)
            hud(disp, f"Click corners in order: {order_label}", 48)
            hud(disp, "[r] reset  [s] save  [q]/ESC quit", 72)
            cv2.imshow(window_name, disp)

        def on_click(event, x, y, _flags, _param):
            if event == cv2.EVENT_LBUTTONDOWN and len(pts) < click_count:
                pts.append((x, y))
                redraw()

        disp = frame.copy()
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(
            window_name,
            min(frame_info.width, self.cfg.arena_points.max_display_width),
            min(frame_info.height, self.cfg.arena_points.max_display_height),
        )
        cv2.setMouseCallback(window_name, on_click)
        redraw()

        while True:
            k = cv2.waitKey(30) & 0xFF
            if k in (27, ord("q")):
                break
            if k == ord("r"):
                pts.clear()
                redraw()
            if k == ord("s"):
                if len(pts) != click_count:
                    self.logger.info("Click %s points before saving", click_count)
                    continue
                self._write_points(pts, frame_info, video_path)
                self.logger.info("Saved %s points to %s", click_count, self.cfg.arena_points.output_h5)

        cv2.destroyAllWindows()


def run_arena_points(cfg: Config, logger) -> None:
    try:
        ArenaPointsAnnotator(cfg, logger).run()
    except Exception as exc:
        logger.error("Arena point annotation failed: %s", exc)
        sys.exit(1)

## python -m dosedynamics arena-points --config configs/default.yaml \
  ## arena_points.video_path="C:\Users\BlackRig-33-1\Desktop\videos_training\20221207_05488_M-003.mp4" \
  ## arena_points.time=60
