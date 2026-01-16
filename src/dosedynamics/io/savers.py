from pathlib import Path
from typing import Optional

import pandas as pd
from matplotlib.figure import Figure


def save_dataframe(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)


def save_figure(fig: Figure, path: Path, dpi: Optional[int] = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=dpi)
