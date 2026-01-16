from __future__ import annotations

from typing import List

import pandas as pd


def extract_body_part(
    df: pd.DataFrame, body_part: str, meta_cols: List[str]
) -> pd.DataFrame:
    if not isinstance(df.columns, pd.MultiIndex):
        raise ValueError("Expected MultiIndex columns in DLC dataframe")

    missing = [c for c in meta_cols if c not in df.columns.get_level_values(0)]
    if missing:
        raise KeyError(f"Missing required metadata columns: {missing}")

    body = df.xs(body_part, axis=1, level="bodyparts")
    body = body.droplevel("scorer", axis=1)

    out = pd.concat([df[meta_cols], body], axis=1)
    out.columns = [col[0] if isinstance(col, tuple) else col for col in out.columns]
    return out
