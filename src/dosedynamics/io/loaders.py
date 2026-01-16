from pathlib import Path

import pandas as pd


def load_h5(path: Path) -> pd.DataFrame:
    return pd.read_hdf(path)
