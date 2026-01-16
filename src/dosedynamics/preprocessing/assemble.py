from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

import cv2
import numpy as np
import pandas as pd

from dosedynamics.config import Config, MetadataFieldConfig
from dosedynamics.preprocessing.transform import transform_dlc_coords_to_cm
from dosedynamics.utils.paths import PathManager


@dataclass
class ParsedMetadata:
    fields: Dict[str, str]


class DLCCombinedBuilder:
    def __init__(self, cfg: Config, logger) -> None:
        self.cfg = cfg
        self.logger = logger
        self.paths = PathManager(cfg)

    def _load_arena_corners(self) -> Dict[str, np.ndarray]:
        arena_path = self.paths.resolve(self.cfg.dataset_build.arena_coords_h5)
        arena_df = pd.read_hdf(arena_path)
        corners = {}
        for video_name, g in arena_df.groupby(self.cfg.dataset_build.arena_video_col):
            ordered = g.sort_values(self.cfg.dataset_build.arena_corner_index_col)
            corners[video_name] = ordered[
                [self.cfg.dataset_build.arena_x_col, self.cfg.dataset_build.arena_y_col]
            ].to_numpy()
        return corners

    def _parse_field(self, field_cfg: MetadataFieldConfig, source_text: str) -> str:
        match = re.search(field_cfg.pattern, source_text)
        if not match:
            raise ValueError(
                f"Pattern '{field_cfg.pattern}' did not match '{source_text}'"
            )
        if field_cfg.name not in match.groupdict():
            raise ValueError(
                f"Pattern '{field_cfg.pattern}' must define '{field_cfg.name}'"
            )
        value = match.group(field_cfg.name)
        return self._apply_transform(value, field_cfg.transform)

    @staticmethod
    def _apply_transform(value: str, transform: str | None) -> str:
        if transform is None or transform == "none":
            return value
        if transform == "first_char":
            return value[0] if value else value
        if transform == "lower":
            return value.lower()
        if transform == "upper":
            return value.upper()
        raise ValueError(f"Unknown transform '{transform}'")

    def _extract_metadata(self, path: Path) -> ParsedMetadata:
        fields: Dict[str, str] = {}
        for field_cfg in self.cfg.dataset_build.metadata_fields:
            source_text = path.name if field_cfg.source == "filename" else str(path)
            fields[field_cfg.name] = self._parse_field(field_cfg, source_text)
        return ParsedMetadata(fields=fields)

    def _build_video_name(self, filename: str) -> str:
        token = self.cfg.dataset_build.video_name.split_token
        stem = filename.split(token)[0]
        return f"{stem}{self.cfg.dataset_build.video_name.extension}"

    def _map_administration(self, animal_id: str) -> str:
        for admin, ids in self.cfg.dataset_build.administration.map.items():
            if animal_id in ids:
                return admin
        return self.cfg.dataset_build.administration.default

    def _apply_perspective_transform(
        self, df: pd.DataFrame, corners: np.ndarray
    ) -> pd.DataFrame:
        src = corners.astype(np.float32)
        dst = np.array(
            [
                [0, 0],
                [self.cfg.arena.width_cm, 0],
                [self.cfg.arena.width_cm, self.cfg.arena.length_cm],
                [0, self.cfg.arena.length_cm],
            ],
            dtype=np.float32,
        )
        matrix = cv2.getPerspectiveTransform(src, dst)
        return transform_dlc_coords_to_cm(df, matrix)

    def run(self) -> None:
        input_dir = self.paths.resolve(self.cfg.dataset_build.input_dir)
        files = sorted(input_dir.rglob(self.cfg.dataset_build.file_glob))
        if not files:
            raise FileNotFoundError(
                f"No files matched {self.cfg.dataset_build.file_glob} in {input_dir}"
            )

        corners_map = self._load_arena_corners()
        output_path = self.paths.resolve(self.cfg.dataset_build.output_h5)

        for path in files:
            self.logger.info("Processing %s", path)
            data = pd.read_hdf(path)
            metadata = self._extract_metadata(path)
            video_name = self._build_video_name(path.name)
            animal_id = metadata.fields.get("animal_id", "")

            data["video_name"] = video_name
            data["administration"] = self._map_administration(animal_id)
            for key, value in metadata.fields.items():
                data[key] = value

            if video_name not in corners_map:
                raise KeyError(f"No arena corners for video '{video_name}'")
            norm_data = self._apply_perspective_transform(data, corners_map[video_name])

            norm_data.to_hdf(
                output_path,
                key=self.cfg.dataset_build.output_key,
                mode=self.cfg.dataset_build.output_mode,
                format=self.cfg.dataset_build.output_format,
                append=self.cfg.dataset_build.append,
            )
